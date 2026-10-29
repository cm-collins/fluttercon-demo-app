package dev.fluttercon.kiln

import android.content.pm.PackageManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "dev.fluttercon.kiln/runtime",
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "rendererFamily" -> result.success(rendererFamily())
                "rendererEvidence" -> result.success(rendererEvidence())
                else -> result.notImplemented()
            }
        }
    }

    private fun rendererFamily(): String {
        val info = packageManager.getApplicationInfo(
            packageName,
            PackageManager.GET_META_DATA,
        )
        return info.metaData?.getString("dev.fluttercon.kiln.RENDERER_FAMILY") ?: "impeller"
    }

    private fun rendererEvidence(): Map<String, Any?> {
        val info = packageManager.getApplicationInfo(
            packageName,
            PackageManager.GET_META_DATA,
        )
        val family = info.metaData?.getString("dev.fluttercon.kiln.RENDERER_FAMILY")
            ?: "impeller"
        return mapOf(
            "family" to family,
            "backend" to null,
            "backendVerified" to false,
            "androidApi" to android.os.Build.VERSION.SDK_INT,
            "device" to "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
        )
    }
}
