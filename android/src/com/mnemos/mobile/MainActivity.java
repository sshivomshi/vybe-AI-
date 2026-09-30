package com.mnemos.mobile;

import android.app.*;
import android.os.Bundle;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import java.util.*;
import java.util.concurrent.*;
import org.json.JSONArray;

public final class MainActivity extends Activity {
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private PhoneStore store; private ApiSettings settings; private String chat;
    private boolean busy,destroyed,savedView;
    private LinearLayout transcript; private ScrollView scroll; private EditText input; private Button send; private TextView status;
    private static final int INK=0xFFECEAF4, ACCENT=0xFFBDA7F5, PAPER=0xFF090B12;
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private GradientDrawable background(int color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));return g;}
    private TextView text(String value,int size){TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(INK);v.setPadding(dp(6),dp(7),dp(6),dp(7));return v;}
    private Button button(String label,View.OnClickListener action){Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(13);b.setTextColor(ACCENT);b.setMinHeight(dp(48));b.setMinimumWidth(0);b.setPadding(dp(12),0,dp(12),0);b.setBackground(new RippleDrawable(android.content.res.ColorStateList.valueOf(0x337F6EA8),background(0xFF191C29,18),null));b.setOnClickListener(action);return b;}
    private void notice(String value){Toast.makeText(this,value,Toast.LENGTH_LONG).show();}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);store=new PhoneStore(this);settings=new ApiSettings(this);chat=settings.prefs.getString("active_chat",UUID.randomUUID().toString());
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(18),dp(6),dp(18),dp(6));root.setBackgroundColor(PAPER);
        LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);
        Button menu=button("☰",v->menu(v));menu.setContentDescription("Open menu");header.addView(menu,new LinearLayout.LayoutParams(dp(48),dp(48)));
        TextView title=text("Vybe AI",21);title.setTypeface(Typeface.create("sans-serif-medium",0));title.setGravity(Gravity.CENTER);header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        Button fresh=button("＋",v->newChat());fresh.setContentDescription("New chat");header.addView(fresh,new LinearLayout.LayoutParams(dp(48),dp(48)));root.addView(header);
        status=text("",12);status.setTextColor(0xFF9E9AAE);status.setGravity(Gravity.CENTER);root.addView(status);
        scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setVerticalScrollBarEnabled(false);transcript=new LinearLayout(this);transcript.setOrientation(1);scroll.addView(transcript);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout composer=new LinearLayout(this);composer.setGravity(Gravity.BOTTOM);composer.setPadding(dp(12),dp(8),dp(8),dp(8));GradientDrawable surface=background(0xFF191C29,28);surface.setStroke(dp(1),0xFF303344);composer.setBackground(surface);
        input=new EditText(this);input.setHint("Message Vybe AI");input.setContentDescription("Message");input.setHintTextColor(0xFF9290A3);input.setBackgroundColor(Color.TRANSPARENT);input.setPadding(dp(6),dp(10),dp(6),dp(10));input.setTextSize(16);input.setMinLines(1);input.setMaxLines(5);input.setTextColor(INK);input.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);input.setText(settings.prefs.getString("draft",""));composer.addView(input,new LinearLayout.LayoutParams(0,-2,1));
        send=button("↑",v->send());send.setTextSize(24);send.setContentDescription("Send message");send.setTextColor(PAPER);send.setBackground(background(ACCENT,24));composer.addView(send,new LinearLayout.LayoutParams(dp(48),dp(48)));root.addView(composer);
        TextView note=text("A little space to think. Chats saved on your phone.",11);note.setGravity(Gravity.CENTER);note.setTextColor(0xFF858397);root.addView(note);setContentView(root);render();
    }
    private void newChat(){if(busy){notice("Wait for the current reply first.");return;}chat=UUID.randomUUID().toString();savedView=false;input.setText("");persistDraft();render();}
    private void compose(String prompt){input.setText(prompt);input.setSelection(input.length());input.requestFocus();((android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).showSoftInput(input,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);}
    private void menu(View anchor){
        if(busy){notice("Wait for the current reply first.");return;}PopupMenu menu=new PopupMenu(this,anchor);
        for(String item:new String[]{"New chat","Chat history","Saved replies","Delete this chat"})menu.getMenu().add(item);
        menu.setOnMenuItemClickListener(item->{String name=item.getTitle().toString();
            if(name.equals("New chat"))newChat();
            else if(name.equals("Chat history"))history();
            else if(name.equals("Saved replies")){savedView=true;render();}
            else new AlertDialog.Builder(this).setTitle("Delete this chat?").setMessage("This removes its messages and saved replies from this phone.").setNegativeButton("Cancel",null).setPositiveButton("Delete",(d,w)->{store.delete(chat);newChat();}).show();return true;
        });menu.show();
    }
    private void history(){List<String[]> rows=store.chats();if(rows.isEmpty()){notice("No saved conversations yet.");return;}String[] labels=new String[rows.size()];for(int i=0;i<labels.length;i++)labels[i]=rows.get(i)[1];new AlertDialog.Builder(this).setTitle("Your conversations").setItems(labels,(d,n)->{chat=rows.get(n)[0];savedView=false;input.setText("");persistDraft();render();}).setNegativeButton("Close",null).show();}
    private void render(){
        transcript.removeAllViews();status.setText(savedView?"Saved replies · available offline":settings.ready()?"Your personal orbit":"Connection unavailable · your draft stays saved");
        if(savedView)transcript.addView(button("Back to conversation",v->{savedView=false;render();}));
        List<String[]> rows=store.messages(chat,savedView);
        if(rows.isEmpty() && !busy){
            if(!savedView)transcript.addView(new SpaceView(this),new LinearLayout.LayoutParams(-1,dp(230)));
            TextView heading=text(savedView?"Your saved discoveries":"Where will your mind go?",28);heading.setTypeface(Typeface.create("sans-serif-medium",0));heading.setGravity(Gravity.CENTER);transcript.addView(heading);
            TextView intro=text(savedView?"Save a useful answer to find it here, even offline.":"Big questions. Small ideas. Endless possibilities.",14);intro.setGravity(Gravity.CENTER);intro.setTextColor(0xFF9E9AAE);transcript.addView(intro);
            if(!savedView){LinearLayout suggestions=new LinearLayout(this);suggestions.setGravity(Gravity.CENTER);suggestions.setPadding(0,dp(20),0,dp(24));LinearLayout.LayoutParams chip=new LinearLayout.LayoutParams(0,dp(48),1);chip.setMargins(dp(4),0,dp(4),0);suggestions.addView(button("Explain a topic",v->compose("Explain a topic to me in simple terms: ")),chip);suggestions.addView(button("Help me write",v->compose("Help me write ")),chip);transcript.addView(suggestions);}
        }
        for(String[] row:rows)addMessage(row[1],row[2],Long.parseLong(row[0]),"1".equals(row[3]));
        if(!savedView && !rows.isEmpty())scroll.post(()->scroll.fullScroll(View.FOCUS_DOWN));
    }
    private void addMessage(String role,String content,long id,boolean saved){
        boolean user=role.equals("user");LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(10),dp(8),dp(10),dp(8));card.setBackground(background(user?0xFF242134:Color.TRANSPARENT,22));LinearLayout.LayoutParams layout=new LinearLayout.LayoutParams(-1,-2);layout.setMargins(user?dp(36):0,dp(10),0,dp(10));transcript.addView(card,layout);
        TextView label=text(user?"You":"✦  Vybe AI",12);label.setTextColor(ACCENT);card.addView(label);TextView body=text(content,16);body.setTextIsSelectable(true);body.setLineSpacing(dp(4),1);card.addView(body);
        if(!user && id>0){LinearLayout actions=new LinearLayout(this);Button save=button(saved?"Saved ✓":"Save reply",null);save.setOnClickListener(v->{boolean next=!save.getText().toString().startsWith("Saved");store.bookmark(id,next);save.setText(next?"Saved ✓":"Save reply");if(savedView)render();});actions.addView(save);Button copy=button("Copy",v->{((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("Vybe AI reply",content));notice("Reply copied");});LinearLayout.LayoutParams gap=new LinearLayout.LayoutParams(-2,-2);gap.setMargins(dp(8),0,0,0);actions.addView(copy,gap);card.addView(actions);}
    }
    private void send(){
        if(busy)return;if(savedView){savedView=false;render();}final String prompt=input.getText().toString().trim();if(prompt.isEmpty())return;if(prompt.length()>16000){notice("Please keep each message under 16,000 characters.");return;}
        if(!settings.ready()){notice("The assistant connection is unavailable. Your message stays here until the connection is restored.");return;}
        final String requestChat=chat,base=settings.base(),model=settings.model();final JSONArray context;final String key;
        try{context=store.context(chat,prompt);key=settings.key();}catch(Exception e){notice("Could not access the assistant connection. Your draft is kept.");return;}
        persistDraft();busy=true;send.setEnabled(false);send.setAlpha(.45f);input.setEnabled(false);render();addMessage("user",prompt,0,false);status.setText("Thinking…");scroll.post(()->scroll.fullScroll(View.FOCUS_DOWN));
        worker.execute(()->{try{String reply=ChatApi.reply(base,model,key,context,attempt->runOnUiThread(()->{if(!destroyed)status.setText("Service busy · retrying "+attempt+" of 3…");}));store.saveExchange(requestChat,prompt,reply);if(requestChat.equals(settings.prefs.getString("active_chat","")) && prompt.equals(settings.prefs.getString("draft","").trim()))settings.prefs.edit().putString("draft","").commit();runOnUiThread(()->{if(destroyed)return;busy=false;send.setEnabled(true);send.setAlpha(1);input.setEnabled(true);input.setText("");persistDraft();render();});}
            catch(Exception error){String message=error instanceof java.net.SocketTimeoutException?"The assistant took too long to reply. Your draft is kept; try again.":error instanceof java.net.UnknownHostException || error instanceof java.net.ConnectException?"Cannot reach the assistant. Check your internet connection.":error instanceof javax.net.ssl.SSLException?"The secure connection could not be verified. Check your phone's date and time.":error instanceof java.io.IOException?error.getMessage():"Could not complete the request. Your draft is kept. Please try again.";runOnUiThread(()->{if(destroyed)return;busy=false;send.setEnabled(true);send.setAlpha(1);input.setEnabled(true);render();status.setText("Request failed · draft kept");new AlertDialog.Builder(this).setTitle("Could not get a reply").setMessage(message).setPositiveButton("OK",null).show();});}
        });
    }
    private void persistDraft(){settings.prefs.edit().putString("active_chat",chat).putString("draft",input.getText().toString()).apply();}
    @Override protected void onPause(){persistDraft();super.onPause();}
    @Override protected void onDestroy(){destroyed=true;worker.execute(()->store.close());worker.shutdown();super.onDestroy();}
    @Override public void onBackPressed(){if(savedView){savedView=false;render();}else super.onBackPressed();}
}
