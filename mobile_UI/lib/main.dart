import 'package:flutter/material.dart';
import 'package:my_app/screens/home/home.dart';
import 'package:my_app/theme.dart';
import 'package:my_app/models/data_from_api.dart';
import 'package:dnsolve/dnsolve.dart';
import 'package:my_app/models/reverse_lookup.dart';
import 'dart:io';
void main() {
  runApp(MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: primaryTheme,
    home: const Home(),
  ));
}

class Sandbox extends StatefulWidget {
  const Sandbox({super.key});

  @override
  State<Sandbox> createState() => _SandboxState();
}

class _SandboxState extends State<Sandbox> {
  final ApiService _apiService = ApiService();
  

  String _status = "Loading...";
  String domain = "Loading...";

  @override
  void initState() {
    super.initState();
    _fetchFirewallData();
    _resolveDomain("54.144.211.88");  // Replace with your IP
  }

  Future<void> _fetchFirewallData() async {
    setState(() {
      _status = "Loading...";
    });

    try {
      final status = await _apiService.getStatus();
      setState(() {
        _status = status ? "Online" : "Offline";
      });
    } catch (e) {
      setState(() {
        _status = "Error: $e";
      });
    }
  }

  Future<void> _resolveDomain(String ip) async {
    final result = await ReverseLookup(ip: ip).resolveIpToDomain(ip);
    setState(() {
      domain = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text(domain),
      ),
    );
  }
}