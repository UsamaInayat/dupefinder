import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Central palette — change colors here to retheme the whole app.
class DupePalette {
  DupePalette._();

  static const Color pink = Color(0xFFFF71A9);
  static const Color pinkDeep = Color(0xFFE91E8C);
  static const Color teal = Color(0xFF3BD6B6);
  static const Color tealWall = Color(0xFF37A8B9);
  static const Color blue = Color(0xFF5B8DEF);
  static const Color blueSoft = Color(0xFF8EB7FF);
  static const Color textPrimary = Color(0xFF2D3748);
  static const Color greySubtitle = Color(0xFF6B7280);
  static const Color greyGuest = Color(0xFF9CA3AF);
  static const Color borderGlass = Color(0x66FFFFFF);
  static const Color scaffoldLight = Color(0xFFF7FAFC);
  static const Color cardSurface = Color(0xFFFFFFFF);

  static LinearGradient get heroGradient => const LinearGradient(
        colors: [pink, blue, teal],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      );

  static LinearGradient get ctaGradient => const LinearGradient(
        colors: [pink, teal],
        begin: Alignment.centerLeft,
        end: Alignment.centerRight,
      );

  static LinearGradient get ctaGradientWide => const LinearGradient(
        colors: [pink, teal, blue],
        begin: Alignment.centerLeft,
        end: Alignment.centerRight,
      );

  static LinearGradient get loginBackgroundGradient => LinearGradient(
        colors: [
          pink.withValues(alpha: 0.45),
          blue.withValues(alpha: 0.35),
          teal.withValues(alpha: 0.4),
        ],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      );

  static TextStyle serifHeading(double size, {FontWeight w = FontWeight.w700, Color? color}) {
    return GoogleFonts.playfairDisplay(
      fontSize: size,
      fontWeight: w,
      color: color ?? Colors.white,
      height: 1.2,
    );
  }
}

/// Legacy names — `const` aliases so existing `const TextStyle(...)` calls stay valid.
/// When retuning, update [DupePalette] first; keep these in sync (or point here to DupePalette consts only).
class AppColors {
  static const Color purpleDark = DupePalette.textPrimary;
  static const Color bluePrimary = DupePalette.blue;
  static const Color blueLight = DupePalette.blueSoft;
  static const Color greySubtitle = DupePalette.greySubtitle;
  static const Color greyGuest = DupePalette.greyGuest;
  static const Color scaffoldBg = DupePalette.scaffoldLight;
  static const Color cardSurface = DupePalette.cardSurface;
  /// Derived alpha — not a const constructor.
  static final Color borderLightBlue = DupePalette.blue.withValues(alpha: 0.35);
}

class AppDecor {
  static const double cardRadius = 20;
  static const double tileRadius = 18;
  static BoxDecoration cardDecoration = BoxDecoration(
    color: AppColors.cardSurface,
    borderRadius: BorderRadius.circular(cardRadius),
    boxShadow: [
      BoxShadow(
        color: DupePalette.pink.withValues(alpha: 0.08),
        blurRadius: 16,
        offset: const Offset(0, 6),
      ),
    ],
  );
  static BoxDecoration welcomeBanner = BoxDecoration(
    gradient: LinearGradient(
      colors: [
        DupePalette.pink.withValues(alpha: 0.15),
        DupePalette.teal.withValues(alpha: 0.12),
      ],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    borderRadius: BorderRadius.circular(cardRadius),
    border: Border.all(color: DupePalette.borderGlass.withValues(alpha: 0.5)),
  );

  /// Frosted glass panel (login card).
  static BoxDecoration glassCard({double radius = 24}) {
    return BoxDecoration(
      borderRadius: BorderRadius.circular(radius),
      color: Colors.white.withValues(alpha: 0.22),
      border: Border.all(color: Colors.white.withValues(alpha: 0.45)),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.06),
          blurRadius: 24,
          offset: const Offset(0, 12),
        ),
      ],
    );
  }
}

class AppTheme {
  static ThemeData dupeFinderTheme() {
    final baseText = GoogleFonts.interTextTheme();
    return ThemeData(
      useMaterial3: true,
      fontFamily: GoogleFonts.inter().fontFamily,
      scaffoldBackgroundColor: AppColors.scaffoldBg,
      colorScheme: ColorScheme.light(
        primary: DupePalette.pink,
        onPrimary: Colors.white,
        secondary: DupePalette.teal,
        onSecondary: Colors.white,
        tertiary: DupePalette.blue,
        surface: Colors.white,
        onSurface: AppColors.purpleDark,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: AppColors.purpleDark,
        elevation: 0,
        centerTitle: true,
        scrolledUnderElevation: 2,
        shadowColor: DupePalette.pink.withValues(alpha: 0.12),
        titleTextStyle: baseText.titleLarge?.copyWith(
          color: AppColors.purpleDark,
          fontWeight: FontWeight.bold,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.cardSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppDecor.cardRadius)),
        shadowColor: DupePalette.pink.withValues(alpha: 0.08),
        margin: const EdgeInsets.only(bottom: 14),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: BorderSide(color: AppColors.borderLightBlue, width: 1.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: BorderSide(color: AppColors.borderLightBlue, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(28),
          borderSide: BorderSide(color: DupePalette.pink, width: 2),
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
          side: BorderSide(color: DupePalette.pink, width: 2),
          foregroundColor: DupePalette.pinkDeep,
        ),
      ),
    );
  }

  static BoxDecoration loginGradientButton = BoxDecoration(
    borderRadius: BorderRadius.circular(32),
    gradient: DupePalette.ctaGradient,
  );
}
