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
}
