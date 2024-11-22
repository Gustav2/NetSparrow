import 'package:flutter/material.dart';
import 'package:my_app/shared/styled_text.dart';
import 'package:collection/collection.dart';


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

  Map<int, bool> advanced = {
    5: false,
    6: false,
    7: true,
    8: false,
  };

  Map<int, bool> experimental = {
    9: false,
    10: false,
    11: false,
    12: false,
  };

  late Map<String, int> initialGeneral;
  late Map<int, bool> initialAdvanced;
  late Map<int, bool> initialExperimental;

  @override
  void initState() {
    super.initState();

    // Store initial states
    initialGeneral = Map.from(general);
    initialAdvanced = Map.from(advanced);
    initialExperimental = Map.from(experimental);
  }

  bool hasChanges() {
    if (!MapEquality().equals(initialGeneral, general)) return true;
    if (!MapEquality().equals(initialAdvanced, advanced)) return true;
    if (!MapEquality().equals(initialExperimental, experimental)) return true;

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

    // Show a snack bar only if there are changes
    if (changesMade && !snackbarShown) {
      snackbarShown = true;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: TextButton(
            onPressed: () {
              // Apply the changes and update initial values
              setState(() {
                initialGeneral = Map.from(general);
                initialAdvanced = Map.from(advanced);
                initialExperimental = Map.from(experimental);
                changesMade = false;  // Reset the changesMade flag
              });

              ScaffoldMessenger.of(context).hideCurrentSnackBar();
              snackbarShown = false;
            },
            child: const Text('Apply changes'),
          ),
          duration: const Duration(days: 1),
        ),
      );
    }
  }

  Future<void> fetch() async {
    // Show snackbar only if there are changes
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
                .maxHeight, // Ensures the background fills the screen height
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
                        .maxHeight, // Ensures the content fills the screen height
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
                                  child: StyledText('Setting ${entry.key}'),
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
                      const StyledHeading('Experimental'),
                      const SizedBox(height: 16),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          children: experimental.entries.map((entry) {
                            return Row(
                              children: [
                                Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: StyledText('Setting ${entry.key}'),
                                ),
                                const Expanded(child: SizedBox()),
                                Switch(
                                  value: entry.value,
                                  onChanged: (bool value) {
                                    setState(() {
                                      experimental[entry.key] = value;
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
