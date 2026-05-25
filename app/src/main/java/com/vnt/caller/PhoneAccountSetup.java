package com.vnt.caller;
import android.content.Context;
import android.net.Uri;
import android.telecom.PhoneAccount;
import android.telecom.PhoneAccountHandle;
import android.telecom.TelecomManager;
import android.util.Log;
import android.content.ComponentName;

public class PhoneAccountSetup {
    private static final String TAG = "PhoneAccount";
    public static final String ACCOUNT_ID = "vnt_phone_account";

    public static PhoneAccountHandle getHandle(Context ctx) {
        return new PhoneAccountHandle(new ComponentName(ctx, VNTConnectionService.class), ACCOUNT_ID);
    }

    public static void register(Context ctx) {
        try {
            TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
            PhoneAccount account = PhoneAccount.builder(getHandle(ctx), "VNT")
                .setCapabilities(PhoneAccount.CAPABILITY_CALL_PROVIDER)
                .setSupportedUriSchemes(java.util.Arrays.asList("tel"))
                .build();
            tm.registerPhoneAccount(account);
            Log.i(TAG, "Registered");
        } catch (Exception e) { Log.e(TAG, e.getMessage()); }
    }

    public static void makeCall(Context ctx, String number) {
        try {
            // Use native dialer with SIM - don't force through VNT account
            android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_CALL);
            intent.setData(Uri.fromParts("tel", number, null));
            intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
            ctx.startActivity(intent);
        } catch (Exception e) { Log.e(TAG, e.getMessage()); }
    }
}
