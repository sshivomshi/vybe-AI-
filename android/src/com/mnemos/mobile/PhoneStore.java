package com.mnemos.mobile;

import android.content.Context;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.*;
import java.util.*;
import org.json.*;

final class PhoneStore extends SQLiteOpenHelper {
    PhoneStore(Context context){super(context,"phone-chats.db",null,1);}
    @Override public void onCreate(SQLiteDatabase db){
        db.execSQL("CREATE TABLE chats(id TEXT PRIMARY KEY,title TEXT NOT NULL,updated INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE messages(id INTEGER PRIMARY KEY AUTOINCREMENT,chat TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,saved INTEGER NOT NULL DEFAULT 0)");
        db.execSQL("CREATE INDEX messages_chat ON messages(chat,id)");
    }
    @Override public void onUpgrade(SQLiteDatabase db,int oldV,int newV){}
    List<String[]> chats(){List<String[]> list=new ArrayList<>();try(Cursor c=getReadableDatabase().rawQuery("SELECT id,title FROM chats ORDER BY updated DESC",null)){while(c.moveToNext())list.add(new String[]{c.getString(0),c.getString(1)});}return list;}
    List<String[]> messages(String chat,boolean saved){
        List<String[]> list=new ArrayList<>();
        String sql=saved?"SELECT id,role,content,saved FROM messages WHERE saved=1 ORDER BY id DESC LIMIT 100":"SELECT id,role,content,saved FROM (SELECT * FROM messages WHERE chat=? ORDER BY id DESC LIMIT 100) ORDER BY id";
        try(Cursor c=getReadableDatabase().rawQuery(sql,saved?null:new String[]{chat})){while(c.moveToNext())list.add(new String[]{c.getString(0),c.getString(1),c.getString(2),c.getString(3)});}return list;
    }
    JSONArray context(String chat,String prompt) throws JSONException {
        List<String[]> list=messages(chat,false); JSONArray result=new JSONArray();
        for(int i=Math.max(0,list.size()-20);i<list.size();i++)result.put(new JSONObject().put("role",list.get(i)[1]).put("content",list.get(i)[2]));
        return result.put(new JSONObject().put("role","user").put("content",prompt));
    }
    void saveExchange(String chat,String prompt,String reply){
        SQLiteDatabase db=getWritableDatabase();db.beginTransaction();
        try {
            ContentValues header=new ContentValues();header.put("id",chat);header.put("title",prompt.substring(0,Math.min(60,prompt.length())));header.put("updated",System.currentTimeMillis());
            db.insertWithOnConflict("chats",null,header,SQLiteDatabase.CONFLICT_IGNORE);
            ContentValues time=new ContentValues();time.put("updated",System.currentTimeMillis());db.update("chats",time,"id=?",new String[]{chat});
            add(db,chat,"user",prompt);add(db,chat,"assistant",reply);db.setTransactionSuccessful();
        }finally{db.endTransaction();}
    }
    private void add(SQLiteDatabase db,String chat,String role,String content){ContentValues row=new ContentValues();row.put("chat",chat);row.put("role",role);row.put("content",content);db.insertOrThrow("messages",null,row);}
    void bookmark(long id,boolean saved){ContentValues v=new ContentValues();v.put("saved",saved?1:0);getWritableDatabase().update("messages",v,"id=?",new String[]{Long.toString(id)});}
    void delete(String chat){SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{db.delete("messages","chat=?",new String[]{chat});db.delete("chats","id=?",new String[]{chat});db.setTransactionSuccessful();}finally{db.endTransaction();}}
}
