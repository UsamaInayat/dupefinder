import 'package:flutter/material.dart';

/// DupeFinder design — purple text, blue gradient CTAs, distinct card style.
class AppColors {
  static const Color purpleDark = Color(0xFF3F3D56);
  static const Color bluePrimary = Color(0xFF4A89F3);
  static const Color blueLight = Color(0xFF6BA3F7);
  static const Color greySubtitle = Color(0xFF6B7280);
  static const Color greyGuest = Color(0xFF9CA3AF);
  static const Color borderLightBlue = Color(0xFFB8D4FC);
  static const Color scaffoldBg = Color(0xFFF5F8FC);
  static const Color cardSurface = Color(0xFFFFFFFF);
}

class AppDecor {
  static const double cardRadius = 20;
  static const double tileRadius = 18;
  static BoxDecoration cardDecoration = BoxDecoration(
    color: AppColors.cardSurface,
    borderRadius: BorderRadius.circular(cardRadius),
    boxShadow: [
      BoxShadow(
        color: AppColors.bluePrimary.withValues(alpha: 0.06),
        blurRadius: 12,
        offset: const Offset(0, 4),
      ),
    ],
  );
  static BoxDecoration welcomeBanner = BoxDecoration(
    gradient: LinearGradient(
      colors: [AppColors.bluePrimary.withValues(alpha: 0.08), AppColors.blueLight.withValues(alpha: 0.05)],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    borderRadius: BorderRadius.circular(cardRadius),
    border: Border.all(color: AppColors.borderLightBlue.withValues(alpha: 0.6)),
  );
}

class AppTheme {
  static ThemeData dupeFinderTheme() {
    return ThemeData(
      useMaterial3: true,
      fontFamily: 'Roboto',
      scaffoldBackgroundColor: AppColors.scaffoldBg,
      colorScheme: ColorScheme.light(
        primary: AppColors.bluePrimary,
        onPrimary: Colors.white,
        secondary: AppColors.purpleDark,
        surface: Colors.white,
        onSurface: AppColors.purpleDark,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.cardSurface,
        foregroundColor: AppColors.purpleDark,
        elevation: 0,
        centerTitle: true,
        scrolledUnderElevation: 2,
        shadowColor: AppColors.bluePrimary.withValues(alpha: 0.1),
        titleTextStyle: const TextStyle(
          color: AppColors.purpleDark,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.cardSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppDecor.cardRadius)),
        shadowColor: AppColors.bluePrimary.withValues(alpha: 0.08),
        margin: const EdgeInsets.only(bottom: 14),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: const BorderSide(color: AppColors.borderLightBlue, width: 1.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: const BorderSide(color: AppColors.borderLightBlue, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: const BorderSide(color: AppColors.bluePrimary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: const BorderSide(color: Colors.redAccent, width: 1.5),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(32),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(32),
          ),
          side: const BorderSide(color: AppColors.bluePrimary, width: 2),
          foregroundColor: AppColors.bluePrimary,
        ),
      ),
    );
  }

  static BoxDecoration loginGradientButton = BoxDecoration(
    borderRadius: BorderRadius.circular(32),
    gradient: const LinearGradient(
      colors: [AppColors.bluePrimary, AppColors.blueLight],
      begin: Alignment.centerLeft,
      end: Alignment.centerRight,
    ),
  );
}
