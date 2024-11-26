import 'package:flutter/material.dart';
import 'package:my_app/shared/styled_text.dart';
import 'package:collection/collection.dart';
import 'package:my_app/theme.dart';


class Settings extends StatefulWidget {
  const Settings({super.key});

  @override
  State<Settings> createState() => _SettingsState();
}

class _SettingsState extends State<Settings> {
  bool changesMade = false;
  bool snackbarShown = false;

  Map<String, int> general = {
    "Caution": 0,
    "Other": 0,
  };

  Map<String, bool> advanced = {
    "Auto add central blacklist entries": true,
    "Log suspicious packets": true,
    "Enable IP blocking": true,
    "Alert new entries": false,
  };

  Map<String, bool> extra = {
    "Dark mode": false,
    "Large icons": false,
    "App animations": false,
    "Color blind mode": false,
  };

  late Map<String, int> initialGeneral;
  late Map<String, bool> initialAdvanced;
  late Map<String, bool> initialExtra;

  @override
  void initState() {
    super.initState();

    initialGeneral = Map.from(general);
    initialAdvanced = Map.from(advanced);
    initialExtra = Map.from(extra);
  }

  bool hasChanges() {
    if (!MapEquality().equals(initialGeneral, general)) return true;
    if (!MapEquality().equals(initialAdvanced, advanced)) return true;
    if (!MapEquality().equals(initialExtra, extra)) return true;

    return false;
  }


  Future<void> showSnackBar() async {
    if (!hasChanges()) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      snackbarShown = false;
      return;
    };

    setState(() {
      changesMade = true;
    });

    if (changesMade && !snackbarShown) {
      snackbarShown = true;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          elevation: 0,
          backgroundColor: Colors.transparent,
          content: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextButton(
                style: ButtonStyle(
                  backgroundColor:WidgetStateProperty.all(AppColors.primaryColor),
                ),
                onPressed: () {
                  setState(() {
                    initialGeneral = Map.from(general);
                    initialAdvanced = Map.from(advanced);
                    initialExtra = Map.from(extra);
                    changesMade = false;
                  });
              
                  ScaffoldMessenger.of(context).hideCurrentSnackBar();
                  snackbarShown = false;
                },
                child: const Text('Apply changes'),
              ),
            ],
          ),
          duration: const Duration(days: 1),
        ),
      );
    }
  }

  Future<void> fetch() async {
    showSnackBar();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const StyledTitle('Settings'),
      ),
      body: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          return Container(
            height: constraints
                .maxHeight,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Color.fromARGB(255, 250, 250, 250),
                  Color.fromARGB(255, 250, 250, 250),
                  Color.fromARGB(255, 240, 240, 240),
                  Color.fromARGB(255, 225, 225, 225),
                  Color.fromARGB(255, 210, 210, 210),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: constraints
                        .maxHeight,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 16),
                      const StyledHeading('General'),
                      const SizedBox(height: 16),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          children: general.entries.map((entry) {
                            return Column(
                              children: [
                                Padding(
                                  padding: const EdgeInsets.only(top: 16),
                                  child: StyledText(entry.key),
                                ),
                                Slider(
                                  value: entry.value.toDouble(),
                                  min: 0,
                                  max: 100,
                                  divisions: 20,
                                  label: entry.value.toString(),
                                  onChanged: (double value) {
                                    setState(() {
                                      general[entry.key] = value.toInt();
                                    });
                                    fetch();
                                  },
                                ),
                              ],
                            );
                          }).toList(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const StyledHeading('Advanced'),
                      const SizedBox(height: 16),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          children: advanced.entries.map((entry) {
                            return Row(
                              children: [
                                Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: StyledText(entry.key),
                                ),
                                const Expanded(child: SizedBox()),
                                Switch(
                                  value: entry.value,
                                  onChanged: (bool value) {
                                    setState(() {
                                      advanced[entry.key] = value;
                                    });
                                    fetch();
                                  },
                                ),
                              ],
                            );
                          }).toList(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const StyledHeading('Appearance'),
                      const SizedBox(height: 16),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          children: extra.entries.map((entry) {
                            return Row(
                              children: [
                                Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: StyledText(entry.key),
                                ),
                                const Expanded(child: SizedBox()),
                                Switch(
                                  value: entry.value,
                                  onChanged: (bool value) {
                                    setState(() {
                                      extra[entry.key] = value;
                                    });
                                    fetch();
                                  },
                                ),
                              ],
                            );
                          }).toList(),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                  )),
            ),
          );
        },
      ),
    );
  }
}
