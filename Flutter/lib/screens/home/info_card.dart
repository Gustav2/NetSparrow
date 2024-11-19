import 'package:flutter/material.dart';
import 'package:my_app/screens/blacklist/blacklist.dart';
import 'package:my_app/screens/log/log.dart';
import 'package:my_app/screens/settings/Settngs.dart';
import 'package:my_app/theme.dart';

class InfoCard extends StatelessWidget {
  const InfoCard(this.info, {super.key});

  final String info;

  @override
  Widget build(BuildContext context) {
    return Card(
        color: AppColors.secondaryColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Text(info),
                const Expanded(child: SizedBox()),
                IconButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => _getRoute(info)),
                    );
                  },
                  icon: Icon(Icons.arrow_forward, color: AppColors.textColor),
                ),
              ],
            ),
          ),
        ));
  }

  Widget _getRoute(String route) {
    if (route == 'Blacklist') return const Blacklist();
    if (route == 'Settings') return const Settings();
    return const Log();
  }
}
