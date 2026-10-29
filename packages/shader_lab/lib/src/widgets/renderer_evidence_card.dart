import 'package:flutter/widgets.dart';

import '../logic/renderer_evidence.dart';
import '../logic/durations.dart';
import 'lab_chrome.dart';
import 'lab_tokens.dart';

/// A deliberately conservative identity panel for renderer experiments.
class RendererEvidenceCard extends StatelessWidget {
  const RendererEvidenceCard({
    super.key,
    required this.evidence,
    required this.rendererLabel,
    required this.budget,
  });

  final RendererEvidence evidence;
  final String rendererLabel;
  final Duration budget;

  @override
  Widget build(BuildContext context) {
    return LabCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              const Expanded(
                child: Text('RENDERER EVIDENCE', style: LabText.label),
              ),
              Text(rendererLabel, style: LabText.number.copyWith(fontSize: 14)),
            ],
          ),
          const SizedBox(height: 12),
          _Line(label: 'ENGINE', value: evidence.engine),
          _Line(label: 'BACKEND', value: evidence.backendLabel),
          _Line(
            label: 'ANDROID',
            value: evidence.androidApi?.toString() ?? 'Unavailable',
          ),
          _Line(label: 'DEVICE', value: evidence.device ?? 'Unavailable'),
          _Line(label: 'BUILD', value: evidence.buildMode),
          _Line(label: 'BUDGET', value: '${formatMs(budget)} ms'),
          const SizedBox(height: 10),
          Text(
            evidence.backendVerified ? 'Backend confirmed by engine evidence.' : 'Backend is not verified in-app. Confirm with adb logcat before making a Vulkan claim.',
            style: LabText.label.copyWith(
              color: evidence.backendVerified
                  ? LabColors.green
                  : LabColors.ember,
            ),
          ),
        ],
      ),
    );
  }
}

class _Line extends StatelessWidget {
  const _Line({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Row(
        children: <Widget>[
          SizedBox(width: 92, child: Text(label, style: LabText.label)),
          Expanded(
            child: Text(
              value,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: LabText.number.copyWith(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }
}
