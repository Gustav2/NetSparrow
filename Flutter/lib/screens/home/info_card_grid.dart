import 'package:flutter/material.dart';

class InfoCardGrid extends StatelessWidget {
  const InfoCardGrid(this.children, {super.key});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: SizedBox(
          height: (children.length / 2).ceil() *
              (165 + 4),
          child: GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 1,
              crossAxisSpacing: 16,
              mainAxisSpacing: 0,
            ),
            itemCount: children.length,
            itemBuilder: (context, index) {
              return Card(
                color: Colors.white,
                surfaceTintColor: Colors.transparent,
                elevation: 1,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: children[index],
                ),
              );
            },
          ),
        ));
  }
}
