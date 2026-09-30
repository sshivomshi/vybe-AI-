package com.mnemos.mobile;

import android.app.Instrumentation;
import android.os.Bundle;
import android.content.Context;
import java.io.File;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import org.json.JSONObject;

/** Explicitly invoked real-device check. Credentials are staged privately, then encrypted. */
final class LiveGeminiCheck {
    static void run(Instrumentation instrumentation) {
        Bundle result=new Bundle();PhoneStore store=null;String key="";
        Context context=instrumentation.getTargetContext();File staged=new File(context.getFilesDir(),"gemini-check.json");
        try {
            if(!staged.isFile() || staged.length()>4096)throw new Exception("Missing private test configuration.");
            byte[] bytes=Files.readAllBytes(staged.toPath());Files.delete(staged.toPath());
            JSONObject config=new JSONObject(new String(bytes,StandardCharsets.UTF_8));java.util.Arrays.fill(bytes,(byte)0);
            key=config.getString("key");
            String base=ChatApi.validateBase(config.optString("base","https://generativelanguage.googleapis.com/v1beta/openai")),model=config.optString("model","gemini-3.1-flash-lite");
            if(model.trim().isEmpty())throw new Exception("Missing configured model.");
            ApiSettings settings=new ApiSettings(context);settings.save(base,model,key,false);
            if(!settings.key().equals(key))throw new Exception("Credential verification failed.");
            store=new PhoneStore(context);String chat="gemini-check-"+UUID.randomUUID();
            String prompt="Reply with exactly: Mnemos Android connection works.";
            String reply=ChatApi.reply(settings.base(),settings.model(),settings.key(),store.context(chat,prompt));
            if(reply.trim().isEmpty())throw new Exception("No reply received.");
            store.saveExchange(chat,prompt,reply);long id=Long.parseLong(store.messages(chat,false).get(1)[0]);store.bookmark(id,true);
            store.close();store=new PhoneStore(context);
            if(store.messages(chat,false).size()!=2 || !store.messages(chat,false).get(1)[2].equals(reply) || !"1".equals(store.messages(chat,false).get(1)[3]))throw new Exception("Saved reply failed persistence check.");
            if(settings.prefs.getString("draft","").trim().isEmpty())settings.prefs.edit().putString("active_chat",chat).commit();
            result.putString("stream","PASS: Real Android HTTPS reply, encrypted credential round-trip, chat saved, reply bookmarked, database reopened successfully. Model: "+model+". Reply: "+reply.replace(key,"[REDACTED]")+"\n");instrumentation.finish(-1,result);
        }catch(Exception error){result.putString("stream","FAIL: "+(error.getMessage()==null?error.getClass().getSimpleName():error.getMessage().replace(key.isEmpty()?"[NO KEY]":key,"[REDACTED]"))+"\n");instrumentation.finish(1,result);}
        finally{if(store!=null)store.close();if(staged.exists())staged.delete();}
    }
}
