import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const FoodCalorieApp());
}

class FoodCalorieApp extends StatelessWidget {
  const FoodCalorieApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Food Calorie Scanner',
      theme: ThemeData(
        primarySwatch: Colors.green,
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}