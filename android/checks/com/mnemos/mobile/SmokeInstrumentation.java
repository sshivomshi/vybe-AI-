package com.mnemos.mobile;

import android.app.Instrumentation;
import android.os.Bundle;
import android.content.*;
import android.database.DatabaseErrorHandler;
import android.database.sqlite.SQLiteDatabase;
import java.net.*;
import java.io.*;
import javax.net.ssl.*;
import java.security.cert.Certificate;
import org.json.*;

/** Device-side checks against isolated storage and a fake HTTPS transport. No provider calls. */
public final class SmokeInstrumentation extends Instrumentation {
    private static int code=200;
    private static int attempts,temporaryFailures;
    private static String payload="{\"choices\":[{\"message\":{\"content\":\"Mock answer\"}}]}";
    private static String errorPayload;
    private static boolean failErrorRead;
    private static FakeConnection connection;
    private boolean live,retryOnly;
    private static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
    private static void checkApiError(JSONArray messages,int status,String body,String expected) throws Exception {
        code=status;errorPayload=body;boolean failed=false;
        try{ChatApi.reply("https://one.example/v1","test-model","test-secret",messages);}
        catch(IOException e){
            failed=true;check(e.getMessage().contains(expected),"Actionable API error: "+expected);
            check(!e.getMessage().contains("test-secret") && !e.getMessage().contains("private-prompt"),"Provider error redaction");
        }
        check(failed,"HTTP error handling");check(connection.disconnected,"Failed request disconnects");
        if(body!=null || failErrorRead)check(connection.errorClosed,"Provider error stream closed");
    }
    private static String googleError(String status,JSONObject... details) throws JSONException {
        JSONArray array=new JSONArray();for(JSONObject detail:details)array.put(detail);
        return new JSONObject().put("error",new JSONObject().put("status",status).put("message","test-secret private-prompt").put("details",array)).toString();
    }
    private static JSONObject reason(String value) throws JSONException {
        return new JSONObject().put("@type","type.googleapis.com/google.rpc.ErrorInfo").put("reason",value)
            .put("metadata",new JSONObject().put("key","test-secret"));
    }
    private static JSONObject retry(String delay) throws JSONException {
        return new JSONObject().put("@type","type.googleapis.com/google.rpc.RetryInfo").put("retryDelay",delay);
    }
    private static JSONObject quota(Object value) throws JSONException {
        return new JSONObject().put("@type","type.googleapis.com/google.rpc.QuotaFailure").put("violations",new JSONArray()
            .put(new JSONObject().put("quotaValue",value).put("quotaId","test-secret").put("description","private-prompt")));
    }
    @Override public void onCreate(Bundle arguments){super.onCreate(arguments);retryOnly=arguments!=null && "true".equals(arguments.getString("retryOnly"));live=arguments!=null && "true".equals(arguments.getString("live"));start();}
    @Override public void onStart(){
        if(live){LiveGeminiCheck.run(this);return;}
        if(retryOnly){
            Bundle result=new Bundle();
            try {
                URL.setURLStreamHandlerFactory(protocol->"https".equals(protocol)?new URLStreamHandler(){@Override protected URLConnection openConnection(URL url){connection=new FakeConnection(url);return connection;}}:null);
                JSONArray messages=new JSONArray().put(new JSONObject().put("role","user").put("content","Hello"));
                temporaryFailures=2;attempts=0;
                check(ChatApi.reply("https://one.example/v1","test-model","test-secret",messages).equals("Mock answer") && attempts==3,"503 recovery");
                temporaryFailures=4;attempts=0;boolean exhausted=false;
                try{ChatApi.reply("https://one.example/v1","test-model","test-secret",messages);}catch(IOException e){exhausted=e.getMessage().contains("3 attempts");}
                check(exhausted && attempts==3,"503 limit");
                temporaryFailures=0;attempts=0;code=401;
                try{ChatApi.reply("https://one.example/v1","test-model","test-secret",messages);}catch(IOException expected){}
                check(attempts==1,"No auth retry");
                result.putString("stream","PASS: 503 recovery, three-attempt limit, no authentication retry.\n");finish(-1,result);
            }catch(Throwable e){result.putString("stream","FAIL: "+e.toString());finish(1,result);}return;
        }
        Bundle report=new Bundle();PhoneStore store=null;
        try{
            Context context=new ContextWrapper(getTargetContext()){
                @Override public android.content.SharedPreferences getSharedPreferences(String name,int mode){return super.getSharedPreferences("smoke-"+name,mode);}
                @Override public SQLiteDatabase openOrCreateDatabase(String name,int mode,SQLiteDatabase.CursorFactory factory,DatabaseErrorHandler handler){return super.openOrCreateDatabase("smoke-"+name,mode,factory,handler);}
            };
            context.deleteDatabase("smoke-phone-chats.db");context.getSharedPreferences("internet-api",0).edit().clear().commit();
            store=new PhoneStore(context);String id="smoke-conversation";
            store.saveExchange(id,"Remember this","A useful reply");check(store.messages(id,false).size()==2,"Exchange persistence");
            long message=Long.parseLong(store.messages(id,false).get(1)[0]);store.bookmark(message,true);check(store.messages(id,true).size()==1,"Saved reply");
            store.close();store=new PhoneStore(context);check(store.messages(id,true).size()==1,"Saved reply survives reopen");
            for(int i=0;i<15;i++)store.saveExchange(id,"Question "+i,"Answer "+i);
            check(store.context(id,"Next").length()==21,"Bounded context plus prompt");
            store.delete(id);check(store.chats().isEmpty() && store.messages(id,true).isEmpty(),"Deletion removes saved replies");
            ApiSettings settings=new ApiSettings(context);settings.save("https://one.example/v1","test-model","test-secret",false);
            check(settings.key().equals("test-secret"),"Keystore round trip");
            check(!settings.prefs.getString("key","").contains("test-secret"),"Credential encrypted");
            settings.save("https://one.example/v1","other-model","",false);check(settings.key().equals("test-secret"),"Same URL keeps credential");
            settings.save("https://two.example/v1","other-model","",false);check(settings.key().isEmpty(),"Changed URL clears credential");
            check(ChatApi.validateBase("https://one.example/v1/chat/completions/").equals("https://one.example/v1"),"Endpoint normalization");
            for(String bad:new String[]{"http://one.example/v1","https://user:pass@one.example/v1","https://one.example/v1?key=x"}){
                boolean rejected=false;try{ChatApi.validateBase(bad);}catch(Exception e){rejected=true;}check(rejected,"Reject unsafe endpoint");
            }
            URL.setURLStreamHandlerFactory(protocol->"https".equals(protocol)?new URLStreamHandler(){@Override protected URLConnection openConnection(URL url){connection=new FakeConnection(url);return connection;}}:null);
            JSONArray messages=new JSONArray().put(new JSONObject().put("role","user").put("content","Hello"));
            check(ChatApi.reply("https://one.example/v1","test-model","test-secret",messages).equals("Mock answer"),"Response parsing");
            check(connection.getURL().getPath().equals("/v1/chat/completions"),"API path");
            check(connection.auth.equals("Bearer test-secret"),"Authorization header");
            check(!connection.getInstanceFollowRedirects(),"No credential forwarding on redirects");
            check(new JSONObject(connection.sent.toString("UTF-8")).getJSONArray("messages").length()==1,"Request JSON");
            checkApiError(messages,401,null,"rejected access");
            checkApiError(messages,429,null,"limit or credit balance");
            checkApiError(messages,500,null,"HTTP 500");
            checkApiError(messages,302,null,"redirects requests");
            checkApiError(messages,400,googleError("INVALID_ARGUMENT",reason("API_KEY_INVALID")),"key is invalid or expired");
            checkApiError(messages,400,googleError("INVALID_ARGUMENT",reason("API_KEY_EXPIRED")),"key is invalid or expired");
            checkApiError(messages,403,googleError("PERMISSION_DENIED",reason("API_KEY_SERVICE_BLOCKED")),"key's API restrictions");
            checkApiError(messages,403,googleError("PERMISSION_DENIED",reason("SERVICE_DISABLED")),"Enable it in the provider console");
            checkApiError(messages,429,googleError("RESOURCE_EXHAUSTED",quota(0),retry("3s")),"no available quota");
            checkApiError(messages,429,googleError("RESOURCE_EXHAUSTED",quota("0")),"no available quota");
            checkApiError(messages,429,googleError("RESOURCE_EXHAUSTED",quota(100),retry("1.5s")),"Wait about 2 seconds");
            checkApiError(messages,429,googleError("RESOURCE_EXHAUSTED"),"Check project usage");
            checkApiError(messages,429,googleError("RESOURCE_EXHAUSTED",retry("test-secret")),"Check project usage");
            checkApiError(messages,429,googleError("RESOURCE_EXHAUSTED",retry("999999s")),"Check project usage");
            checkApiError(messages,400,"{\"error\":{\"message\":\"test-secret private-prompt\"}}","Check the base URL, model ID");
            checkApiError(messages,500,"not JSON: test-secret private-prompt","HTTP 500");
            checkApiError(messages,403,googleError("PERMISSION_DENIED",new JSONObject().put("@type","other.ErrorInfo").put("reason","API_KEY_INVALID")),"rejected access");
            StringBuilder oversized=new StringBuilder(googleError("INVALID_ARGUMENT",reason("API_KEY_INVALID")));
            while(oversized.length()<=64*1024)oversized.append(' ');
            checkApiError(messages,400,oversized.toString(),"Check the base URL, model ID");
            check(connection.errorBytesRead==64*1024+1,"Bounded provider error read");
            failErrorRead=true;checkApiError(messages,500,"test-secret","HTTP 500");failErrorRead=false;errorPayload=null;
            code=200;errorPayload=null;attempts=0;temporaryFailures=2;
            check(ChatApi.reply("https://one.example/v1","test-model","test-secret",messages).equals("Mock answer"),"503 recovery");
            check(attempts==3,"503 retries twice then succeeds");
            attempts=0;temporaryFailures=4;
            boolean exhausted=false;try{ChatApi.reply("https://one.example/v1","test-model","test-secret",messages);}catch(IOException e){exhausted=e.getMessage().contains("3 attempts");}
            check(exhausted && attempts==3,"503 retry limit");temporaryFailures=0;
            code=200;payload="{\"choices\":[{\"message\":{\"content\":null}}]}";
            boolean empty=false;try{ChatApi.reply("https://one.example/v1","test-model","",messages);}catch(IOException e){empty=true;}check(empty,"Empty response rejected");
            settings.prefs.edit().clear().commit();
            report.putString("stream","PASS: SQLite history/bookmarks/reopen/delete, context limits, Android Keystore credentials, endpoint validation, HTTPS request/response, sanitized provider errors and bounded error reads. Mock transport only.\n");finish(-1,report);
        }catch(Throwable error){report.putString("stream","FAIL: "+error.toString()+"\n");finish(1,report);}finally{if(store!=null)store.close();getTargetContext().deleteDatabase("smoke-phone-chats.db");}
    }
    static final class FakeConnection extends HttpsURLConnection {
        final ByteArrayOutputStream sent=new ByteArrayOutputStream();String auth;int errorBytesRead;boolean errorClosed,disconnected;
        FakeConnection(URL url){super(url);}
        @Override public void setRequestProperty(String key,String value){if(key.equals("Authorization"))auth=value;super.setRequestProperty(key,value);}
        @Override public OutputStream getOutputStream(){return sent;}
        @Override public int getResponseCode(){attempts++;return temporaryFailures-->0?503:code;}
        @Override public InputStream getInputStream(){return new ByteArrayInputStream(payload.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
        @Override public InputStream getErrorStream(){
            if(errorPayload==null && !failErrorRead)return null;
            return new FilterInputStream(new ByteArrayInputStream((errorPayload==null?"":errorPayload).getBytes(java.nio.charset.StandardCharsets.UTF_8))){
                @Override public int read(byte[] buffer,int offset,int length) throws IOException {
                    if(failErrorRead)throw new IOException("test-secret");
                    int count=in.read(buffer,offset,length);if(count>0)errorBytesRead+=count;return count;
                }
                @Override public void close() throws IOException {errorClosed=true;super.close();}
            };
        }
        @Override public void disconnect(){disconnected=true;} @Override public boolean usingProxy(){return false;} @Override public void connect(){}
        @Override public String getCipherSuite(){return "mock";} @Override public Certificate[] getLocalCertificates(){return null;} @Override public Certificate[] getServerCertificates(){return null;}
    }
}
