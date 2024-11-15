import 'package:flutter/material.dart';
import 'package:my_app/shared/styled_text.dart';
import 'package:my_app/theme.dart';

class LogCard extends StatelessWidget {
  const LogCard(
    this.timestamp,
    this.speed,
    this.latency,
    {super.key});

  final int speed;
  final int latency;
  final String timestamp;


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
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                //color: AppColors.primaryColor,
                padding: const EdgeInsets.all(8),
                child: StyledText(timestamp)),
              //const Expanded(child: SizedBox()),
              Text('$speed Mb/s'),
              Text('$latency ms'),
            ],
          ),
        ),
      )
    );
  }
}
