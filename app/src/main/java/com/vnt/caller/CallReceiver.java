package com.vnt.caller;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.telephony.TelephonyManager;

public class CallReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        String state = intent.getStringExtra(TelephonyManager.EXTRA_STATE);
        String number = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER);
        
        if (!TelephonyManager.EXTRA_STATE_RINGING.equals(state) || number == null) return;
        
        // Check which SIM slot this call came in on
        int slot = intent.getIntExtra("slot", -1);
        if (slot == -1) slot = intent.getIntExtra("simSlot", -1);
        if (slot == -1) slot = intent.getIntExtra("android.telephony.extra.SLOT_INDEX", -1);
        if (slot == -1) slot = intent.getIntExtra("com.android.phone.extra.slot", -1);
        
        // Get user-selected SIM slot from preferences
        SharedPreferences prefs = ctx.getSharedPreferences("vnt_prefs", Context.MODE_PRIVATE);
        int selectedSlot = prefs.getInt("selected_sim_slot", 1); // default eSIM (slot 1)
        
        // Only intercept if it matches selected SIM, or if slot detection failed
        if (slot != -1 && slot != selectedSlot) {
            return; // Wrong SIM - ignore this call
        }
        
        String clean = number.replaceAll("[+\\s-]","");
        String room = clean.endsWith("568116899") ? "ryan-alias" : "vnt-general";
        Intent si = new Intent(ctx, CallService.class);
        si.putExtra("room", room);
        si.putExtra("number", number);
        ctx.startForegroundService(si);
    }
}
