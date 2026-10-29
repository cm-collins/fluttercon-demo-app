import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

import 'kiln_app.dart';
import 'kiln_runtime.dart';

/// Launcher for the Binance market dashboard.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final KilnRuntime runtime = KilnScope.of(context);
    final Duration budget = budgetFor(View.of(context).display.refreshRate);
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Expanded(
                    child: Text('Kiln Markets', style: LabText.title),
                  ),
                  const SizedBox(width: 12),
                  LabBadge(label: runtime.label),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                '${View.of(context).display.refreshRate.round()} Hz · ${formatMs(budget)} ms budget · ${KilnScope.benchmarkModeOf(context) ? 'BENCHMARK' : 'LIVE'}',
                style: LabText.label,
              ),
              const SizedBox(height: 24),
              _Entry(
                title: 'Shader Storm',
                subtitle: 'Dozens of new effects in one frame: JIT vs AOT',
                onTap: () => Navigator.of(context).pushNamed(KilnRoutes.storm),
              ),
              const SizedBox(height: 12),
              _Entry(
                title: 'Markets',
                subtitle: 'Binance book, one shader timed',
                onTap: () =>
                    Navigator.of(context).pushNamed(KilnRoutes.shaderLab),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Entry extends StatelessWidget {
  const _Entry({required this.title, required this.subtitle, this.onTap});

  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final bool enabled = onTap != null;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: LabCard(
        child: Row(
          children: <Widget>[
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: LabText.body.copyWith(
                      fontWeight: FontWeight.w600,
                      color: enabled
                          ? LabColors.textPrimary
                          : LabColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(subtitle, style: LabText.label),
                ],
              ),
            ),
            if (enabled)
              const Text(
                '›',
                style: TextStyle(
                  color: LabColors.violet,
                  fontSize: 28,
                  height: 1,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
