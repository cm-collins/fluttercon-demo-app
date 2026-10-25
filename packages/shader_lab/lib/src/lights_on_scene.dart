import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';

import 'lab_tokens.dart';

/// The scene revealed by Lights on: many effects drawn for the first time at once.
///
/// Each distinct blend mode, gradient type, clip, blur and the custom fragment
/// shader needs its own GPU program. Skia generates and compiles those on first
/// use; Impeller ships them precompiled. Nothing in the surrounding Shader Lab
/// chrome may use these effects, or they would be warmed up before the tap.
class LightsOnScene extends StatefulWidget {
  const LightsOnScene({super.key, required this.program});

  final ui.FragmentProgram program;

  @override
  State<LightsOnScene> createState() => _LightsOnSceneState();
}

class _LightsOnSceneState extends State<LightsOnScene>
    with SingleTickerProviderStateMixin {
  late final AnimationController _clock = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 6),
  )..repeat();
  late final ui.FragmentShader _shader = widget.program.fragmentShader();

  @override
  void dispose() {
    _clock.dispose();
    _shader.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: <Widget>[
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: RadialGradient(
              center: Alignment(0, -0.6),
              radius: 1.2,
              colors: <Color>[Color(0xFF1B1430), LabColors.bg],
            ),
          ),
        ),
        RepaintBoundary(
          child: CustomPaint(painter: _SweepRingPainter(_clock)),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const _GradientTitle(),
              const SizedBox(height: 12),
              SizedBox(
                height: 48,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: RepaintBoundary(
                    child: CustomPaint(
                      painter: _SpeedRampPainter(_shader, _clock),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Expanded(
                child: Stack(
                  fit: StackFit.expand,
                  children: <Widget>[
                    _EffectGrid(),
                    Align(
                      alignment: Alignment.bottomCenter,
                      child: _GlassPanel(),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _GradientTitle extends StatelessWidget {
  const _GradientTitle();

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      blendMode: BlendMode.srcIn,
      shaderCallback: (Rect bounds) => const LinearGradient(
        colors: <Color>[LabColors.ember, LabColors.red, LabColors.aurora],
      ).createShader(bounds),
      child: const Text(
        'LIGHTS ON',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: LabColors.textPrimary,
          fontSize: 40,
          fontWeight: FontWeight.w800,
          letterSpacing: 6,
          shadows: <Shadow>[
            Shadow(color: Color(0x88FF4D6D), blurRadius: 18),
          ],
        ),
      ),
    );
  }
}

const List<BlendMode> _modes = <BlendMode>[
  BlendMode.multiply,
  BlendMode.screen,
  BlendMode.overlay,
  BlendMode.darken,
  BlendMode.lighten,
  BlendMode.colorDodge,
  BlendMode.colorBurn,
  BlendMode.hardLight,
  BlendMode.softLight,
  BlendMode.difference,
  BlendMode.exclusion,
  BlendMode.hue,
  BlendMode.saturation,
  BlendMode.color,
  BlendMode.luminosity,
  BlendMode.plus,
];

const List<Color> _tints = <Color>[
  LabColors.ember,
  LabColors.aurora,
  LabColors.violet,
  LabColors.red,
  LabColors.green,
  LabColors.yellow,
  LabColors.purple,
];

class _EffectGrid extends StatelessWidget {
  const _EffectGrid();

  static const int _columns = 4;

  @override
  Widget build(BuildContext context) {
    final int rows = _modes.length ~/ _columns;
    return Column(
      children: <Widget>[
        for (int r = 0; r < rows; r++)
          Expanded(
            child: Row(
              children: <Widget>[
                for (int c = 0; c < _columns; c++)
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(5),
                      child: _EffectTile(index: r * _columns + c),
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

class _EffectTile extends StatelessWidget {
  const _EffectTile({required this.index});

  final int index;

  Gradient get _gradient {
    final Color a = _tints[index % _tints.length];
    final Color b = _tints[(index + 3) % _tints.length];
    switch (index % 3) {
      case 0:
        return LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[a, b],
        );
      case 1:
        return RadialGradient(colors: <Color>[a, b, LabColors.bg]);
      default:
        return SweepGradient(colors: <Color>[a, b, a]);
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget tile = ColorFiltered(
      colorFilter: ColorFilter.mode(
        _tints[(index + 5) % _tints.length],
        _modes[index],
      ),
      child: DecoratedBox(decoration: BoxDecoration(gradient: _gradient)),
    );

    if (index == 7) {
      tile = ImageFiltered(
        imageFilter: ui.ImageFilter.blur(sigmaX: 4, sigmaY: 4),
        child: tile,
      );
    }
    if (index == 15) {
      tile = ColorFiltered(
        colorFilter: const ColorFilter.matrix(<double>[
          0.2126, 0.7152, 0.0722, 0, 0, //
          0.2126, 0.7152, 0.0722, 0, 0, //
          0.2126, 0.7152, 0.0722, 0, 0, //
          0, 0, 0, 1, 0,
        ]),
        child: tile,
      );
    }

    switch (index % 4) {
      case 1:
        tile = ClipPath(
          clipper: const _ChevronClipper(),
          clipBehavior: Clip.antiAlias,
          child: tile,
        );
      case 3:
        tile = ClipOval(clipBehavior: Clip.antiAlias, child: tile);
      default:
        tile = ClipRRect(
          borderRadius: BorderRadius.circular(12),
          clipBehavior: Clip.antiAlias,
          child: tile,
        );
    }

    if (index % 5 == 0) {
      tile = DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: _tints[index % _tints.length],
              blurRadius: 14,
            ),
          ],
        ),
        child: tile,
      );
    }
    return tile;
  }
}

class _ChevronClipper extends CustomClipper<Path> {
  const _ChevronClipper();

  @override
  Path getClip(Size size) {
    final double w = size.width;
    final double h = size.height;
    return Path()
      ..moveTo(0, 0)
      ..lineTo(w * 0.7, 0)
      ..lineTo(w, h / 2)
      ..lineTo(w * 0.7, h)
      ..lineTo(0, h)
      ..lineTo(w * 0.3, h / 2)
      ..close();
  }

  @override
  bool shouldReclip(_ChevronClipper oldClipper) => false;
}

class _GlassPanel extends StatelessWidget {
  const _GlassPanel();

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: BackdropFilter(
        filter: ui.ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          height: 64,
          decoration: BoxDecoration(
            color: const Color(0x33171B24),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0x55F2F4F8)),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: <Widget>[
              _Sector(label: 'S1', color: LabColors.purple),
              _Sector(label: 'S2', color: LabColors.green),
              _Sector(label: 'S3', color: LabColors.yellow),
            ],
          ),
        ),
      ),
    );
  }
}

class _Sector extends StatelessWidget {
  const _Sector({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: LabText.number.copyWith(color: color, fontSize: 20),
    );
  }
}

class _SweepRingPainter extends CustomPainter {
  _SweepRingPainter(this.clock) : super(repaint: clock);

  final Animation<double> clock;

  @override
  void paint(Canvas canvas, Size size) {
    final Offset center = Offset(size.width / 2, size.height * 0.42);
    final double radius = size.shortestSide * 0.46;
    final Rect rect = Rect.fromCircle(center: center, radius: radius);
    final Paint ring = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
      ..shader = SweepGradient(
        colors: const <Color>[
          Color(0x00B26BFF),
          LabColors.purple,
          LabColors.aurora,
          Color(0x004FD1FF),
        ],
        transform: GradientRotation(clock.value * 2 * math.pi),
      ).createShader(rect);
    canvas.drawCircle(center, radius, ring);
  }

  @override
  bool shouldRepaint(_SweepRingPainter oldDelegate) => false;
}

class _SpeedRampPainter extends CustomPainter {
  _SpeedRampPainter(this.shader, this.clock) : super(repaint: clock);

  final ui.FragmentShader shader;
  final Animation<double> clock;

  @override
  void paint(Canvas canvas, Size size) {
    shader
      ..setFloat(0, size.width)
      ..setFloat(1, size.height)
      ..setFloat(2, clock.value * 6);
    canvas.drawRect(Offset.zero & size, Paint()..shader = shader);
  }

  @override
  bool shouldRepaint(_SpeedRampPainter oldDelegate) => false;
}
