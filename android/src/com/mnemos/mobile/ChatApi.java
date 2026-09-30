package com.mnemos.mobile;

import java.net.URL;
import java.net.URI;
import java.io.*;
import java.nio.charset.StandardCharsets;
import javax.net.ssl.HttpsURLConnection;
import org.json.*;

final class ChatApi {
    private static final int MAX_ERROR_BYTES=64*1024;
    // Provider text can echo credentials or prompts. Only recognized structured fields
    // select messages below; raw messages, metadata, and response bodies are never shown.
    private static JSONObject errorDetails(HttpsURLConnection connection) {
        try(InputStream input=connection.getErrorStream()) {
            if(input==null)return null;
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int read;
            while((read=input.read(buffer,0,Math.min(buffer.length,MAX_ERROR_BYTES+1-bytes.size())))!=-1) {
                if(bytes.size()+read>MAX_ERROR_BYTES)return null;
                bytes.write(buffer,0,read);
            }
            return new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8)).optJSONObject("error");
        }catch(IOException | JSONException e){return null;}
    }
    private static String providerError(JSONObject error) {
        if(error==null)return null;
        boolean invalidKey=false,blockedKey=false,disabledService=false,quota=false,zeroQuota=false;
        long retrySeconds=0;
        JSONArray details=error.optJSONArray("details");
        for(int i=0;details!=null && i<details.length();i++) {
            JSONObject detail=details.optJSONObject(i);if(detail==null)continue;
            String type=detail.optString("@type","");
            if(type.equals("type.googleapis.com/google.rpc.ErrorInfo")) {
                String reason=detail.optString("reason","");
                invalidKey|=reason.equals("API_KEY_INVALID") || reason.equals("API_KEY_EXPIRED");
                blockedKey|=reason.equals("API_KEY_SERVICE_BLOCKED");
                disabledService|=reason.equals("SERVICE_DISABLED");
            } else if(type.equals("type.googleapis.com/google.rpc.QuotaFailure")) {
                quota=true;JSONArray violations=detail.optJSONArray("violations");
                for(int j=0;violations!=null && j<violations.length();j++) {
                    JSONObject violation=violations.optJSONObject(j);
                    if(violation!=null && "0".equals(violation.optString("quotaValue","")))zeroQuota=true;
                }
            } else if(type.equals("type.googleapis.com/google.rpc.RetryInfo")) {
                String delay=detail.optString("retryDelay","");
                if(delay.matches("[0-9]{1,6}(\\.[0-9]{1,9})?s")) {
                    long seconds=(long)Math.ceil(Double.parseDouble(delay.substring(0,delay.length()-1)));
                    if(seconds>0 && seconds<=86400)retrySeconds=Math.max(retrySeconds,seconds);
                }
            }
        }
        if(invalidKey)return "The API key is invalid or expired. Please contact the app administrator.";
        if(blockedKey)return "This API key is blocked from using the requested service. Check the key's API restrictions in your provider project.";
        if(disabledService)return "The requested API is disabled for your provider project. Enable it in the provider console, then retry.";
        if(zeroQuota)return "The provider reports no available quota for this model. Check your project quota, billing, and model access before retrying.";
        if(quota || "RESOURCE_EXHAUSTED".equals(error.optString("status",""))) {
            if(retrySeconds>0)return "The provider's quota or rate limit was reached. Wait about "+retrySeconds+" seconds, then retry. If it continues, check project quota and billing.";
            return "The provider's quota or rate limit was reached. Check project usage, quota limits, and billing, or wait for the quota to reset.";
        }
        return null;
    }
    static String validateBase(String raw) throws Exception {
        String base=raw.trim().replaceAll("/+$","");
        URI u=new URI(base);
        if(!"https".equalsIgnoreCase(u.getScheme()) || u.getHost()==null || u.getUserInfo()!=null || u.getQuery()!=null || u.getFragment()!=null)
            throw new IOException("Enter an HTTPS API base URL without credentials, query, or fragment.");
        if(base.endsWith("/chat/completions"))base=base.substring(0,base.length()-17);
        return base;
    }
    interface RetryListener { void retrying(int attempt); }
    private static final class Unavailable extends IOException {}
    static String reply(String base,String model,String key,JSONArray messages) throws Exception {
        return reply(base,model,key,messages,attempt->{});
    }
    static String reply(String base,String model,String key,JSONArray messages,RetryListener listener) throws Exception {
        for(int attempt=1;attempt<=3;attempt++) {
            try { return request(base,model,key,messages); }
            catch(Unavailable error) {
                if(attempt==3)throw new IOException("The AI service is temporarily unavailable after 3 attempts. Your draft is kept. Please try again later.");
                listener.retrying(attempt+1);
                try { Thread.sleep(attempt*2000L); }
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("Request cancelled. Your draft is kept.");}
            }
        }
        throw new IOException("The AI service is unavailable.");
    }
    private static String request(String base,String model,String key,JSONArray messages) throws Exception {
        if(key.indexOf('\n')>=0 || key.indexOf('\r')>=0) throw new IOException("The API key contains an invalid line break. Please contact the app administrator.");
        HttpsURLConnection connection=(HttpsURLConnection)new URL(validateBase(base)+"/chat/completions").openConnection();
        connection.setInstanceFollowRedirects(false); connection.setConnectTimeout(20000); connection.setReadTimeout(90000);
        connection.setRequestMethod("POST"); connection.setDoOutput(true);
        connection.setRequestProperty("Content-Type","application/json"); connection.setRequestProperty("Accept","application/json");
        if(!key.isEmpty())connection.setRequestProperty("Authorization","Bearer "+key);
        byte[] body=new JSONObject().put("model",model).put("messages",messages).put("stream",false).toString().getBytes(StandardCharsets.UTF_8);
        connection.setFixedLengthStreamingMode(body.length);
        try {
            try(OutputStream output=connection.getOutputStream()){output.write(body);}
            int status=connection.getResponseCode();
            if(status<200 || status>=300) {
                String detail=status>=400?providerError(errorDetails(connection)):null;
                if(detail!=null)throw new IOException(detail);
                if(status==503)throw new Unavailable();
                if(status==401 || status==403)throw new IOException("The API rejected access. Check your API key and model permissions.");
                if(status==429)throw new IOException("The API limit or credit balance was reached. Check your provider account, then retry.");
                if(status>=300 && status<400)throw new IOException("This API redirects requests. Please contact the app administrator.");
                if(status==400 || status==404)throw new IOException("The API could not accept this request. Check the base URL, model ID, and Chat Completions compatibility.");
                throw new IOException("The AI service returned HTTP "+status+". Try again later.");
            }
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            try(InputStream input=connection.getInputStream()) {
                byte[] buffer=new byte[8192]; int read;
                while((read=input.read(buffer))!=-1){if(bytes.size()+read>2*1024*1024)throw new IOException("The AI response is too large.");bytes.write(buffer,0,read);}
            }
            try {
                JSONObject message=new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8)).getJSONArray("choices").getJSONObject(0).getJSONObject("message");
                String content=message.optString("content","");
                if(message.isNull("content") || content.trim().isEmpty()) throw new IOException("The API returned no text response. Try another text model.");
                return content;
            }catch(JSONException e){throw new IOException("The API response does not match Chat Completions. Check your provider settings.");}
        } finally { connection.disconnect(); }
    }
}
