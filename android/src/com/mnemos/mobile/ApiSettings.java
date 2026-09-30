package com.mnemos.mobile;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** User-supplied credentials; encryption keys never leave Android Keystore. */
final class ApiSettings {
    final SharedPreferences prefs;
    ApiSettings(Context context) { prefs=context.getSharedPreferences("internet-api",Context.MODE_PRIVATE); }
    String base() { return prefs.getString("base",""); }
    String model() { return prefs.getString("model",""); }
    boolean ready() { return !base().isEmpty() && !model().isEmpty(); }
    private SecretKey encryptionKey() throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        String alias="mnemos-api-credential";
        if(!store.containsAlias(alias)) {
            KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
            generator.generateKey();
        }
        return (SecretKey)store.getKey(alias,null);
    }
    String key() throws Exception {
        String encrypted=prefs.getString("key",""); if(encrypted.isEmpty())return "";
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE,encryptionKey(),new GCMParameterSpec(128,Base64.decode(prefs.getString("iv",""),Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(encrypted,Base64.NO_WRAP)),java.nio.charset.StandardCharsets.UTF_8);
    }
    void save(String base,String model,String replacement,boolean clear) throws Exception {
        SharedPreferences.Editor edit=prefs.edit().putString("base",base).putString("model",model);
        // A saved credential must never silently move to another endpoint.
        if(clear || !base.equals(base())) edit.remove("key").remove("iv");
        if(!replacement.isEmpty()) {
            Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE,encryptionKey());
            edit.putString("key",Base64.encodeToString(cipher.doFinal(replacement.getBytes(java.nio.charset.StandardCharsets.UTF_8)),Base64.NO_WRAP));
            edit.putString("iv",Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP));
        }
        if(!edit.commit())throw new java.io.IOException("Could not save settings");
    }
}
