import 'package:flutter/material.dart';

class BlacklistMenu extends StatelessWidget {
  const BlacklistMenu({
    required this.addAll,
    required this.removeAll,
    super.key});

  final VoidCallback addAll;
  final VoidCallback removeAll;

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton(
      icon: const Icon(Icons.menu),
      itemBuilder: (BuildContext context) => <PopupMenuEntry>[
        PopupMenuItem(
          child: TextButton(onPressed: () {addAll();}, child: const Text('Add all entries')),
        ),
        PopupMenuItem(
          child: TextButton(onPressed: () {removeAll();}, child: const Text('Remove all entries')),
        ),
      ],
    );
  }
}