package com.vnt.caller;
import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.view.accessibility.AccessibilityEvent;
import android.view.KeyEvent;

public class CallAnswerService extends AccessibilityService {
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // Auto-answer is triggered via performGlobalAction
    }
    
    @Override
    public boolean onKeyEvent(KeyEvent event) {
        return super.onKeyEvent(event);
    }
    
    @Override
    public void onInterrupt() {}
    
    // Called by CallReceiver to answer the call
    public static CallAnswerService instance;
    
    @Override
    public void onServiceConnected() {
        instance = this;
    }
    
    public void answerCall() {
        // Simulate pressing the answer button
        performGlobalAction(GLOBAL_ACTION_BACK);
    }
}
