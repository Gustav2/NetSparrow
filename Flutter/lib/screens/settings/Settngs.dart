import 'package:flutter/material.dart';
import 'package:my_app/shared/styled_text.dart';

class Settings extends StatefulWidget {
  const Settings({super.key});

  @override
  State<Settings> createState() => _SettingsState();
}

class _SettingsState extends State<Settings> {

  Map<int, bool> general = {
    1 : false,
    2: false,
    3: false,
    4: false,
  };

  Map<int, bool> advanced = {
    5: false,
    6: false,
    7: false,
    8: false,
  };

  Map<int, bool> experimental = {
    9: false,
    10: false,
    11: false,
    12: false,
  };


  void function(int index) {
    setState(() {

    });
    print('Function called for index: $index');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
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
                        children: 
                          general.entries.map((entry) {
                            return CheckboxListTile(
                              title: Text('Setting ${entry.key}'),
                              value: entry.value,
                              onChanged: (bool? value) {
                                setState(() {
                                  general[entry.key] = value!;
                                });
                              },
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
                        children: 
                          advanced.entries.map((entry) {
                            return CheckboxListTile(
                              title: Text('Setting ${entry.key}'),
                              value: entry.value,
                              onChanged: (bool? value) {
                                setState(() {
                                  advanced[entry.key] = value!;
                                });
                              },
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
                        children: 
                          experimental.entries.map((entry) {
                            return CheckboxListTile(
                              title: Text('Setting ${entry.key}'),
                              value: entry.value,
                              onChanged: (bool? value) {
                                setState(() {
                                  experimental[entry.key] = value!;
                                });
                              },
                            );
                          }).toList(),
                      ),
                    ),

                    const SizedBox(height: 16),
                  ],
                )
              ),
            ),
          );
        },
      ),
    );
  }
}