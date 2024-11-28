import 'package:flutter/material.dart';
import 'package:my_app/screens/home/home.dart';
import 'package:my_app/theme.dart';
import 'package:my_app/screens/login/login.dart';

void main() {
  runApp(MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: primaryTheme,
    home: const Home(),
  ));
}