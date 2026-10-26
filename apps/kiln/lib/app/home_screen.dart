import 'package:flutter/material.dart';
import 'package:shader_lab/shader_lab.dart';

import 'kiln_build_config.dart';
import 'kiln_app.dart';

/// Temporary launcher until Lights Out and Pit Wall exist.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const Text(
                'Kiln: Pit Wall',
                style: TextStyle(
                  color: LabColors.textPrimary,
                  fontSize: 32,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                '${KilnBuildConfig.rendererLabel} · 120 Hz · 8.33 ms',
                style: LabText.label,
              ),
              const SizedBox(height: 32),
              _Entry(
                title: 'Shader Lab',
                subtitle: 'First-use shader cost, timed',
                onTap: () =>
                    Navigator.of(context).pushNamed(KilnRoutes.shaderLab),
              ),
              const SizedBox(height: 12),
              const _Entry(
                title: 'Pit Wall',
                subtitle: 'Laps 1 to 4 — not built yet',
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
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: LabColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: enabled ? LabColors.violet : LabColors.hairline,
          ),
        ),
        child: Row(
          children: <Widget>[
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: LabText.title.copyWith(
                      fontSize: 20,
                      color: enabled
                          ? LabColors.textPrimary
                          : LabColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      color: LabColors.textSecondary,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
            if (enabled)
              const Icon(Icons.chevron_right, color: LabColors.violet),
          ],
        ),
      ),
    );
  }
}
