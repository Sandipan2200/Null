class FoodAnalysis {
  final String foodName;
  final double confidence;
  final String serving;
  final double caloriesKcal;
  final Macros macros;
  final Micros micros;
  final List<String> sources;
  final String? imageUrl;

  FoodAnalysis({
    required this.foodName,
    required this.confidence,
    required this.serving,
    required this.caloriesKcal,
    required this.macros,
    required this.micros,
    required this.sources,
    this.imageUrl,
  });

  factory FoodAnalysis.fromJson(Map<String, dynamic> json) {
    return FoodAnalysis(
      foodName: json['food_name'] ?? '',
      confidence: (json['confidence'] ?? 0).toDouble(),
      serving: json['serving'] ?? '100g',
      caloriesKcal: (json['calories_kcal'] ?? 0).toDouble(),
      macros: Macros.fromJson(json['macros'] ?? {}),
      micros: Micros.fromJson(json['micros'] ?? {}),
      sources: List<String>.from(json['sources'] ?? []),
      imageUrl: json['image_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'food_name': foodName,
      'confidence': confidence,
      'serving': serving,
      'calories_kcal': caloriesKcal,
      'macros': macros.toJson(),
      'micros': micros.toJson(),
      'sources': sources,
      'image_url': imageUrl,
    };
  }

  @override
  String toString() {
    return 'FoodAnalysis{foodName: $foodName, confidence: $confidence, serving: $serving, caloriesKcal: $caloriesKcal, macros: $macros, micros: $micros, sources: $sources, imageUrl: $imageUrl}';
  }
}

class Macros {
  final double proteinG;
  final double fatG;
  final double carbsG;

  Macros({
    required this.proteinG,
    required this.fatG,
    required this.carbsG,
  });

  factory Macros.fromJson(Map<String, dynamic> json) {
    return Macros(
      proteinG: (json['protein_g'] ?? 0).toDouble(),
      fatG: (json['fat_g'] ?? 0).toDouble(),
      carbsG: (json['carbs_g'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'protein_g': proteinG,
      'fat_g': fatG,
      'carbs_g': carbsG,
    };
  }

  double get totalMacros => proteinG + fatG + carbsG;

  // Calculate calories from macros (4 kcal/g protein, 4 kcal/g carbs, 9 kcal/g fat)
  double get caloriesFromMacros => (proteinG * 4) + (carbsG * 4) + (fatG * 9);

  @override
  String toString() {
    return 'Macros{proteinG: $proteinG, fatG: $fatG, carbsG: $carbsG}';
  }
}

class Micros {
  final double? vitaminCMg;
  final double? calciumMg;
  final double? ironMg;
  final double? vitaminDMcg;
  final double? vitaminB12Mcg;
  final double? magnesiumMg;
  final double? potassiumMg;
  final double? sodiumMg;
  final double? fiberG;
  final double? sugarG;

  Micros({
    this.vitaminCMg,
    this.calciumMg,
    this.ironMg,
    this.vitaminDMcg,
    this.vitaminB12Mcg,
    this.magnesiumMg,
    this.potassiumMg,
    this.sodiumMg,
    this.fiberG,
    this.sugarG,
  });

  factory Micros.fromJson(Map<String, dynamic> json) {
    return Micros(
      vitaminCMg: json['vitamin_c_mg']?.toDouble(),
      calciumMg: json['calcium_mg']?.toDouble(),
      ironMg: json['iron_mg']?.toDouble(),
      vitaminDMcg: json['vitamin_d_mcg']?.toDouble(),
      vitaminB12Mcg: json['vitamin_b12_mcg']?.toDouble(),
      magnesiumMg: json['magnesium_mg']?.toDouble(),
      potassiumMg: json['potassium_mg']?.toDouble(),
      sodiumMg: json['sodium_mg']?.toDouble(),
      fiberG: json['fiber_g']?.toDouble(),
      sugarG: json['sugar_g']?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'vitamin_c_mg': vitaminCMg,
      'calcium_mg': calciumMg,
      'iron_mg': ironMg,
      'vitamin_d_mcg': vitaminDMcg,
      'vitamin_b12_mcg': vitaminB12Mcg,
      'magnesium_mg': magnesiumMg,
      'potassium_mg': potassiumMg,
      'sodium_mg': sodiumMg,
      'fiber_g': fiberG,
      'sugar_g': sugarG,
    };
  }

  bool get hasAnyMicronutrients {
    return vitaminCMg != null ||
        calciumMg != null ||
        ironMg != null ||
        vitaminDMcg != null ||
        vitaminB12Mcg != null ||
        magnesiumMg != null ||
        potassiumMg != null ||
        sodiumMg != null ||
        fiberG != null ||
        sugarG != null;
  }

  @override
  String toString() {
    return 'Micros{vitaminCMg: $vitaminCMg, calciumMg: $calciumMg, ironMg: $ironMg, vitaminDMcg: $vitaminDMcg, vitaminB12Mcg: $vitaminB12Mcg, magnesiumMg: $magnesiumMg, potassiumMg: $potassiumMg, sodiumMg: $sodiumMg, fiberG: $fiberG, sugarG: $sugarG}';
  }
}