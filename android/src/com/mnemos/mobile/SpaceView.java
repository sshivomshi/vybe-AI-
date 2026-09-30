package com.mnemos.mobile;

import android.content.Context;
import android.graphics.*;
import android.view.View;
import android.animation.ValueAnimator;
import android.view.animation.LinearInterpolator;
import java.util.Random;

/** Lightweight procedural scene; no network, textures, or per-frame bitmap allocation. */
final class SpaceView extends View {
    private final Paint paint=new Paint(3);
    private final RectF orbit=new RectF();
    private final float[] stars=new float[180];
    private final ValueAnimator animator=ValueAnimator.ofFloat(0,1);
    private float phase;
    SpaceView(Context context){
        super(context);setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        Random random=new Random(19);for(int i=0;i<stars.length;i++)stars[i]=random.nextFloat();
        animator.setDuration(24000);animator.setRepeatCount(ValueAnimator.INFINITE);animator.setInterpolator(new LinearInterpolator());
        animator.addUpdateListener(a->{phase=(Float)a.getAnimatedValue();invalidate();});
    }
    private void syncAnimation(){
        if(isAttachedToWindow() && getWindowVisibility()==VISIBLE && isShown() && ValueAnimator.areAnimatorsEnabled()) {if(!animator.isStarted())animator.start();}
        else animator.cancel();
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();syncAnimation();}
    @Override protected void onDetachedFromWindow(){animator.cancel();super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);if(animator!=null)syncAnimation();}
    @Override protected void onVisibilityChanged(View view,int visibility){super.onVisibilityChanged(view,visibility);if(animator!=null)syncAnimation();}
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){
        // Shader is allocated only on resize, not for every animation frame.
        super.onSizeChanged(w,h,oldw,oldh);
        glow=new RadialGradient(w*.5f,h*.48f,Math.max(1,w*.48f),new int[]{0x005E5189,0x405E5189,0x005E5189},new float[]{0,.48f,1},Shader.TileMode.CLAMP);
    }
    private Shader glow;
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);float w=getWidth(),h=getHeight(),cx=w*.5f,cy=h*.48f,r=Math.min(w*.19f,h*.27f);
        paint.setStyle(Paint.Style.FILL);paint.setShader(null);
        for(int i=0;i<stars.length;i+=3){paint.setColor(Color.argb((int)(65+95*(.5+.5*Math.sin(phase*Math.PI*2+stars[i]*12))),191,193,220));canvas.drawCircle(stars[i]*w,stars[i+1]*h,.7f+stars[i+2]*1.2f,paint);}
        paint.setShader(glow);canvas.drawCircle(cx,cy,w*.48f,paint);paint.setShader(null);
        canvas.save();canvas.rotate(-19,cx,cy);paint.setStyle(Paint.Style.STROKE);
        for(int i=30;i>=0;i--){float extent=r*(1.35f+i*.027f);orbit.set(cx-extent,cy-extent*.27f,cx+extent,cy+extent*.27f);paint.setStrokeWidth(i<5?2.2f:1.1f);paint.setColor(Color.argb(35+(30-i)*4,166+i*2,144+i*2,240));canvas.drawOval(orbit,paint);}
        paint.setStyle(Paint.Style.FILL);paint.setColor(0xFF030409);canvas.drawCircle(cx,cy,r,paint);
        paint.setStyle(Paint.Style.STROKE);
        for(int i=9;i>=0;i--){paint.setStrokeWidth(1.5f);paint.setColor(Color.argb(18+(9-i)*17,194,174,255));canvas.drawCircle(cx,cy,r+i*.8f,paint);}
        for(int i=0;i<12;i++){float extent=r*(1.4f+i*.047f);orbit.set(cx-extent,cy-extent*.27f,cx+extent,cy+extent*.27f);paint.setColor(Color.argb(130-i*7,218,199,255));paint.setStrokeWidth(1.7f);canvas.drawArc(orbit,phase*360+i*14,35,false,paint);}
        canvas.restore();paint.setStyle(Paint.Style.FILL);
    }
}
