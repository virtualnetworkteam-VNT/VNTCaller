package com.vnt.caller;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class BridgeReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        String number = intent.getStringExtra("number");
        Log.i("BridgeReceiver", "Starting AI bridge for: " + number);
        VNTConnection conn = new VNTConnection(ctx);
        if (number != null) conn.startAIBridge(number);
    }
}
