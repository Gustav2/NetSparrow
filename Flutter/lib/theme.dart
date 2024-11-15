import 'package:flutter/material.dart';

class AppColors {
  static Color primaryColor = const Color(0xff9ce8cb);
  static Color primaryAccent = const Color(0xff5bd7a5);
  static Color secondaryColor = const Color(0xffffffff);
  static Color secondaryAccent = const Color(0xffffffff);
  static Color titleColor = const Color(0xff000000);
  static Color alternativeTextColor = const Color(0xffffffff);
  static Color textColor = const Color(0xff000000);
  //static Color successColor = const Color(0xff5cc3ff);
  //static Color highlightColor = const Color(0xfff4d07c);
}

ThemeData primaryTheme = ThemeData(
  fontFamily: 'Poppins',

  // seed color
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.secondaryColor,
  ),

  // scaffold color
  scaffoldBackgroundColor: AppColors.secondaryAccent,

  // app bar theme colors
  appBarTheme: AppBarTheme(
    //backgroundColor: AppColors.secondaryColor,
    backgroundColor: const Color.fromARGB(255, 250, 250, 250),
    elevation: 20,
    foregroundColor: AppColors.textColor,
    centerTitle: true,
    surfaceTintColor: Colors.transparent,
    scrolledUnderElevation: 3,
  ),
  textTheme: TextTheme(
    bodyMedium: TextStyle(
      color: AppColors.textColor,
      fontSize: 14,
      letterSpacing: 1,
    ),
    headlineMedium: TextStyle(
      color: AppColors.textColor,
      fontSize: 16,
      fontWeight: FontWeight.bold,
      letterSpacing: 1,
    ),
    titleMedium: TextStyle(
      color: AppColors.titleColor,
      fontSize: 22,
      fontWeight: FontWeight.bold,
      letterSpacing: 2,
    ),
    headlineLarge: TextStyle(
      color: AppColors.textColor,
      fontSize: 28,
      fontWeight: FontWeight.bold,
      letterSpacing: 1,
    ), 
  ),

  // card theme
  cardTheme: CardTheme(
      color: AppColors.secondaryColor.withOpacity(0.5),
      surfaceTintColor: Colors.transparent,
      shape: const RoundedRectangleBorder(),
      shadowColor: Colors.transparent,
      margin: const EdgeInsets.only(bottom: 16)),
);
