import 'dart:io';
import 'package:flutter/material.dart';
import '../models/food_analysis.dart';

class ResultScreen extends StatelessWidget {
  final FoodAnalysis foodAnalysis;
  final File imageFile;

  const ResultScreen({
    super.key,
    required this.foodAnalysis,
    required this.imageFile,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text(
          'Analysis Results',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: Colors.green[600],
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildImageCard(),
            const SizedBox(height: 20),
            _buildFoodInfoCard(),
            const SizedBox(height: 20),
            _buildNutritionCard(),
            const SizedBox(height: 20),
            _buildMacrosCard(),
            const SizedBox(height: 20),
            _buildSourcesCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildImageCard() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(15),
        child: Image.file(
          imageFile,
          height: 200,
          fit: BoxFit.cover,
        ),
      ),
    );
  }

  Widget _buildFoodInfoCard() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.fastfood, color: Colors.orange[600], size: 28),
                const SizedBox(width: 12),
                const Text(
                  'Food Identification',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 15),
            _buildInfoRow(
              'Food Name:',
              _formatFoodName(foodAnalysis.foodName),
              Colors.black87,
            ),
            const SizedBox(height: 8),
            _buildInfoRow(
              'Confidence:',
              '${foodAnalysis.confidence.toStringAsFixed(1)}%',
              _getConfidenceColor(),
            ),
            const SizedBox(height: 8),
            _buildInfoRow(
              'Serving Size:',
              foodAnalysis.serving,
              Colors.black54,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionCard() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.local_fire_department, color: Colors.red[600], size: 28),
                const SizedBox(width: 12),
                const Text(
                  'Calories',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 15),
            Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.red[200]!),
                ),
                child: Column(
                  children: [
                    Text(
                      foodAnalysis.caloriesKcal.toStringAsFixed(0),
                      style: TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.bold,
                        color: Colors.red[600],
                      ),
                    ),
                    Text(
                      'kcal',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        color: Colors.red[600],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMacrosCard() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.pie_chart, color: Colors.blue[600], size: 28),
                const SizedBox(width: 12),
                const Text(
                  'Macronutrients',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(child: _buildMacroItem('Protein', foodAnalysis.macros.proteinG, Colors.green)),
                Expanded(child: _buildMacroItem('Fat', foodAnalysis.macros.fatG, Colors.orange)),
                Expanded(child: _buildMacroItem('Carbs', foodAnalysis.macros.carbsG, Colors.blue)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMacroItem(String name, double value, Color color) {
    return Column(
      children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: color.withAlpha((0.1 * 255).toInt()),
                    borderRadius: BorderRadius.circular(10),
                  ),
          child: Column(
            children: [
              Text(
                '${value.toStringAsFixed(1)}g',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                name,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSourcesCard() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.source, color: Colors.purple[600], size: 28),
                const SizedBox(width: 12),
                const Text(
                  'Data Sources',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 15),
            ...foodAnalysis.sources.map((source) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green[600], size: 16),
                  const SizedBox(width: 8),
                  Text(
                    source,
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, Color valueColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.black54,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: valueColor,
          ),
        ),
      ],
    );
  }

  String _formatFoodName(String name) {
    return name.replaceAll('_', ' ').split(' ').map((word) {
      return word.isNotEmpty
          ? word[0].toUpperCase() + word.substring(1).toLowerCase()
          : word;
    }).join(' ');
  }

  Color _getConfidenceColor() {
    if (foodAnalysis.confidence >= 80) {
      return Colors.green[600]!;
    } else if (foodAnalysis.confidence >= 60) {
      return Colors.orange[600]!;
    } else {
      return Colors.red[600]!;
    }
  }
}