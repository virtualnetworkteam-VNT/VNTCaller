package com.vnt.caller;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.telephony.TelephonyManager;

public class CallReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        String state = intent.getStringExtra(TelephonyManager.EXTRA_STATE);
        String number = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER);
        if (TelephonyManager.EXTRA_STATE_RINGING.equals(state) && number != null) {
            String clean = number.replaceAll("[+\\s-]","");
            String room = clean.endsWith("568116899") ? "ryan-alias" : "vnt-general";
            Intent si = new Intent(ctx, CallService.class);
            si.putExtra("room", room);
            si.putExtra("number", number);
            ctx.startForegroundService(si);
        }
    }
}
