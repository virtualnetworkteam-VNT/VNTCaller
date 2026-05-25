package com.vnt.caller;
import android.content.ComponentName;
import android.content.Context;
import android.net.Uri;
import android.os.Bundle;
import android.telecom.PhoneAccount;
import android.telecom.PhoneAccountHandle;
import android.telecom.TelecomManager;
import android.util.Log;

public class PhoneAccountSetup {
    private static final String TAG = "PhoneAccount";
    public static final String ACCOUNT_ID = "vnt_phone_account";

    public static PhoneAccountHandle getHandle(Context ctx) {
        return new PhoneAccountHandle(new android.content.ComponentName(ctx, VNTConnectionService.class), ACCOUNT_ID);
    }

    public static void register(Context ctx) {
        try {
            TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
            PhoneAccount account = PhoneAccount.builder(getHandle(ctx), "VNT AI")
                .setCapabilities(PhoneAccount.CAPABILITY_CALL_PROVIDER)
                .setSupportedUriSchemes(java.util.Arrays.asList("tel", "sip"))
                .build();
            tm.registerPhoneAccount(account);
            Log.i(TAG, "Registered");
        } catch (Exception e) { Log.e(TAG, e.getMessage()); }
    }

    public static void makeCall(Context ctx, String number) {
        try {
            TelecomManager tm = (TelecomManager) ctx.getSystemService(Context.TELECOM_SERVICE);
            Bundle b = new Bundle();
            b.putParcelable(TelecomManager.EXTRA_PHONE_ACCOUNT_HANDLE, getHandle(ctx));
            tm.placeCall(Uri.fromParts("tel", number, null), b);
        } catch (Exception e) { Log.e(TAG, e.getMessage()); }
    }
}
