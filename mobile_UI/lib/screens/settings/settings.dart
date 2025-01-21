import 'package:flutter/material.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:my_app/shared/styled_text.dart';
import 'package:collection/collection.dart';
import 'package:my_app/theme.dart';

class Settings extends StatefulWidget {
  const Settings({super.key});

  @override
  State<Settings> createState() => _SettingsState();
}

class _SettingsState extends State<Settings> {
  final ApiService apiService = ApiService();
  bool changesMade = false;
  bool snackbarShown = false;

  Map<String, dynamic> sliders = {
    "mlPercentage": 10,
    "mlCaution": 0.5,
  };

  Map<String, bool> extra = {
    "Dark mode": false,
    "Large icons": false,
    "App animations": false,
    "Color blind mode": false,
  };

  Map<String, dynamic> realsettings = {
    "...": false,
    "... ": false,
    "...  ": false,
    "...   ": false,
    "...    ": false,
    "...     ": false
  };

  late Map<String, dynamic> initialSliders;
  late Map<String, bool> initialExtra;
  late Map<String, dynamic> initialreal;

  @override
  void initState() {
    super.initState();

    fetchSettingsData();

    initialSliders = Map.from(sliders);
    initialExtra = Map.from(extra);
    initialreal = Map.from(realsettings);
  }

  bool hasChanges() {
    if (!MapEquality().equals(initialSliders, sliders)) return true;
    if (!MapEquality().equals(initialExtra, extra)) return true;
    if (!MapEquality().equals(initialreal, realsettings)) return true;

    return false;
  }

  Future<void> postSettingsData() async {
    try {
      Map<String, dynamic> postData = {};
      Map<String, dynamic> finalData = {};

      realsettings.forEach((key, value) {
        postData[key] = value;
      });

      sliders.forEach((key, value) {
        postData[key] = value;
      });

      print(postData);

      postData.forEach((key, value) {
        String newKey = key.replaceAll(' ', '_').toLowerCase();
        finalData[newKey] = value;
      });

      print(finalData);

      await apiService.postSettings(finalData);
    } catch (e) {
      print(e);
    }
  }

  Future<void> showSnackBar() async {
    if (!hasChanges()) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      snackbarShown = false;
      return;
    }
    ;

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
                  backgroundColor:
                      WidgetStateProperty.all(AppColors.primaryColor),
                ),
                onPressed: () {
                  setState(() {
                    initialSliders = Map.from(sliders);
                    initialExtra = Map.from(extra);
                    initialreal = Map.from(realsettings);
                    changesMade = false;
                    postSettingsData();
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

  Future<void> fetchSettingsData() async {
    try {
      Map<String, dynamic> settingsData = await apiService.getSettings();

      Map<String, dynamic> sl = {};
      Map<String, dynamic> rs = {};

      settingsData.forEach((key, value) {
        if (settingsData[key] is bool) {
          rs[key] = value; 
        } else if (settingsData[key] is int) {
          sl["mlPercentage"] = value;
        } else {
          sl["mlCaution"] = double.parse(value);
        }
      });

      setState(() {
        realsettings = Map.from(rs);
        sliders = Map.from(sl);
        initialreal = Map.from(realsettings);
        initialSliders = Map.from(sliders);
      });
    } catch (e) {
      print("error");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: fetchSettingsData,
          icon: const Icon(Icons.sync),
        ),
        title: const StyledTitle('Settings'),
      ),
      body: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          return Container(
            height: constraints.maxHeight,
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
                    minHeight: constraints.maxHeight,
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
                        child: Column(children: [
                          const Padding(
                            padding: EdgeInsets.only(top: 16),
                            child: StyledText("ML percentage"),
                          ),
                          Slider(
                            value: sliders["mlPercentage"].toDouble(),
                            min: 0,
                            max: 100,
                            divisions: 20,
                            label: sliders["mlPercentage"].toString(),
                            onChanged: (double value) {
                              setState(() {
                                sliders["mlPercentage"] = value.round();
                              });
                              fetch();
                            },
                          ),
                          const Padding(
                            padding: EdgeInsets.only(bottom: 16),
                            child: StyledText('ML Caution'),
                          ),
                          Slider(
                            value: sliders["mlCaution"].toDouble(),
                            min: 0,
                            max: 1,
                            divisions: 10,
                            label: sliders["mlCaution"].toString(),
                            onChanged: (double value) {
                              setState(() {
                                sliders["mlCaution"] = value;
                              });
                              fetch();
                            },
                          ),
                        ]),
                      ),
                      const SizedBox(height: 16),
                      const StyledHeading('Settings'),
                      const SizedBox(height: 16),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          children: realsettings.entries.map((entry) {
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
                                      realsettings[entry.key] = value;
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
