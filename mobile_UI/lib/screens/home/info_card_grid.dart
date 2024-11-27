import 'package:flutter/material.dart';

/// A grid of information cards that displays children in a 2-column layout.
class InfoCardGrid extends StatelessWidget {
  // Constants for layout calculations
  static const double _cardPadding = 16.0;
  static const double _gridSpacing = 16.0;
  static const double _cardHeight = 165.0;
  static const int _columnsCount = 2;

  const InfoCardGrid(this.children, {super.key});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Padding(
        padding: const EdgeInsets.symmetric(horizontal: _cardPadding),
        child: SizedBox(
          height: (children.length / _columnsCount).ceil() * (_cardHeight + _gridSpacing),
          child: GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: _columnsCount,
              childAspectRatio: 1,
              crossAxisSpacing: _gridSpacing,
              mainAxisSpacing: _gridSpacing,
            ),
            itemCount: children.length,
            itemBuilder: (context, index) {
              return Card(
                color: Colors.white,
                surfaceTintColor: Colors.transparent,
                elevation: 1,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(_cardPadding),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(_cardPadding),
                  child: children[index],
                ),
              );
            },
          ),
        ));
  }
}
