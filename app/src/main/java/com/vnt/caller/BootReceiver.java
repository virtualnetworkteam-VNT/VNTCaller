package com.vnt.caller;
import android.content.*;
public class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context ctx, Intent i) {
        ctx.startForegroundService(new Intent(ctx, CallService.class));
    }
}
