# Save this as hmi_app.py
from flask import Flask, render_template_string, send_from_directory, redirect, url_for, request
import webbrowser
import threading
import time
import os

app = Flask(__name__)

# Define the directory for static files (like sounds)
# This assumes your 'static' folder is in the same directory as app.py
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# --- HTML Content for the Main HMI (Dashboard Layout) ---
HMI_HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-lang-key="title">Autonomous Shuttle HMI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'); /* Added 800 for extra bold */

        body {
            font-family: 'Inter', sans-serif;
            overflow: hidden; /* Prevent scrolling */
        }

        /* Common style for the main display frame on both Dashboard and Apps Menu */
        .display-frame {
            transition: filter 0.3s ease-in-out;
            width: 100vw; /* Take full viewport width */
            height: 100vh; /* Take full viewport height */
            max-width: 1280px; /* Max width for larger displays, maintains proportions */
            max-height: 800px; /* Adjust height to maintain a consistent aspect ratio (e.g., 16:10 or 16:9 on common tablets) */
            border-radius: 2.5rem; /* More rounded corners for the whole interface */
            overflow: hidden; /* Ensure content stays within rounded corners */
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 40px 80px rgba(0, 0, 0, 0.5); /* Deeper main shadow */
        }

        /* Custom gradient background for the whole HMI - applied to body for consistent environment */
        .hmi-background {
            background: linear-gradient(135deg, #101c2a 0%, #1c2a3b 100%); /* Even deeper, richer blue-gray gradient */
            position: relative;
            overflow: hidden;
            background-size: 400% 400%;
            animation: gradient-animation 25s ease infinite;
        }

        @keyframes gradient-animation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Dynamic animated glowing dots/particles - applied to body for consistent environment */
        .hmi-background::before,
        .hmi-background::after {
            content: '';
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            filter: blur(80px); /* Increased blur for softer glow */
            opacity: 0.20; /* Slightly less opaque for subtler effect */
        }

        .hmi-background::before {
            width: 350px; /* Larger */
            height: 350px;
            background: #2196f3; /* Stronger blue glow */
            top: 10%; /* Adjusted position */
            left: 5%;
            animation: glow-move-one 25s infinite alternate ease-in-out; /* Slightly different animation speed */
        }

        .hmi-background::after {
            width: 300px; /* Larger */
            height: 300px;
            background: #00e5ff; /* Brighter teal glow for connectivity */
            bottom: 8%; /* Adjusted position */
            right: 5%;
            animation: glow-move-two 30s infinite alternate-reverse ease-in-out; /* Slightly different animation speed */
        }

        @keyframes glow-move-one {
            0% { transform: translate(0, 0); }
            50% { transform: translate(60vw, 40vh); }
            100% { transform: translate(0, 0); }
        }

        @keyframes glow-move-two {
            0% { transform: translate(0, 0); }
            50% { transform: translate(-50vw, -30vh); }
            100% { transform: translate(0, 0); }
        }

        /* New subtle pulse animation for active states/highlights */
        @keyframes pulse-subtle {
            0%, 100% { opacity: 1; text-shadow: 0 0 5px rgba(66, 165, 245, 0.4); }
            50% { opacity: 0.8; text-shadow: 0 0 10px rgba(66, 165, 245, 0.8); }
        }


        /* Card/Widget styling for dashboard elements - Deeper inset and subtle highlight */
        .dashboard-card {
            @apply bg-gray-900 p-6 rounded-2xl shadow-inner border border-gray-700 relative; /* Darker base, shadow-inner for recessed feel */
            background: linear-gradient(160deg, #2a3d50, #1a242f); /* Darker and more contrasted gradient */
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6), /* Inset dark shadow */
                        inset 0 -2px 4px rgba(255, 255, 255, 0.05), /* Subtle inset highlight */
                        0 8px 15px rgba(0, 0, 0, 0.4); /* Outer floating shadow */
            transition: all 0.2s ease-in-out;
        }
        .dashboard-card:hover {
            transform: translateY(-2px); /* Slight lift on hover */
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.7),
                        inset 0 -2px 4px rgba(255, 255, 255, 0.08),
                        0 12px 25px rgba(0, 0, 0, 0.6);
        }

        /* Button styling for bottom row - adapted for icon-text side-by-side */
        .hmi-button {
            @apply relative flex items-center justify-center p-4 rounded-xl shadow-lg transition-all duration-300 ease-in-out transform;
            background: linear-gradient(145deg, #374151, #1f2937); /* Keep dark neutral base */
            border: 1px solid rgba(255, 255, 255, 0.12); /* Slightly stronger border */
            color: #e0e7eb; /* Slightly brighter text color */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2),
                        0 10px 20px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.08); /* Stronger inner highlight */
            flex-direction: row; /* Default for bottom buttons */
        }

        /* Specific hmi-button adjustments for the Apps Menu page */
        .apps-menu-container .hmi-button { /* Target buttons ONLY within the apps menu container */
            flex-direction: column; /* Back to column for tile menu */
            min-height: 150px; /* Ensure buttons have enough space */
        }
        .apps-menu-container .hmi-button-icon { /* Target icons ONLY within the apps menu container */
            @apply text-5xl mr-0 mb-3; /* Larger icon for tile menu, no right margin, add bottom margin */
        }
        .apps-menu-container .hmi-button-text { /* Target text ONLY within the apps menu container */
            @apply text-xl;
        }


        .hmi-button:hover {
            transform: translateY(-3px) scale(1.06); /* More pronounced lift and scale */
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.35),
                        0 15px 30px rgba(0, 0, 0, 0.45),
                        inset 0 1px 0 rgba(255, 255, 255, 0.15); /* Stronger hover highlight */
            @apply focus:outline-none focus:ring-4 focus:ring-[#42a5f5] focus:ring-opacity-70; /* Slightly more opaque ring */
        }

        .hmi-button:active {
            transform: scale(0.97); /* Slightly more compression */
            box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.6), /* Deeper inset on press */
                        inset 0 -1px 2px rgba(255, 255, 255, 0.05);
        }

        .hmi-button-icon {
            @apply text-3xl mr-3; /* Adjusted size and margin for horizontal layout */
            color: #42a5f5; /* New vibrant blue accent */
            text-shadow: 0 0 15px rgba(66, 165, 245, 0.9); /* Stronger icon glow */
        }

        .hmi-button-text {
            @apply text-xl font-semibold;
            text-shadow: 0 0 8px rgba(224, 231, 235, 0.5); /* Stronger text glow */
        }

        /* Specific emergency button style */
        .hmi-button.emergency {
            background: linear-gradient(145deg, #dc2626, #b91c1c); /* Red gradient */
            color: #fff;
        }
        .hmi-button.emergency .hmi-button-icon {
            color: #fff;
            text-shadow: 0 0 15px rgba(220, 38, 38, 0.9); /* Stronger red glow */
        }

        /* Map Placeholder Animations */
        @keyframes blob-slow {
            0%, 100% { transform: translate(0, 0) scale(1); }
            30% { transform: translate(20%, 10%) scale(1.2); }
            60% { transform: translate(-10%, 20%) scale(0.9); }
            80% { transform: translate(15%, -5%) scale(1.1); }
        }

        @keyframes blob-fast {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25% { transform: translate(-15%, -10%) scale(1.1); }
            50% { transform: translate(5%, 15%) scale(0.8); }
            75% { transform: translate(10%, -10%) scale(1.2); }
        }

        @keyframes bounce-subtle {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); /* More pronounced bounce */ }
        }


        /* Modal/Overlay styling for HVAC, System Preferences */
        .modal-overlay {
            @apply fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 transition-opacity duration-300 ease-in-out; /* Darker overlay */
        }

        .modal-content {
            @apply bg-gray-800 p-10 rounded-3xl shadow-2xl w-full max-w-lg mx-4 border border-gray-700 relative;
            background: linear-gradient(160deg, #2a3d50, #1c2a3b); /* Consistent with new background */
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4),
                        0 20px 40px rgba(0, 0, 0, 0.5),
                        inset 0 2px 0 rgba(255, 255, 255, 0.1); /* Stronger inner highlight */
        }

        .modal-close-button {
            @apply absolute top-5 right-5 text-gray-400 hover:text-white text-4xl focus:outline-none;
        }

        /* Slider styling with glow - updated accent color */
        input[type="range"] {
            -webkit-appearance: none;
            width: 100%;
            height: 12px; /* Slightly thicker slider */
            background: #4a5568;
            border-radius: 6px;
            outline: none;
            transition: opacity .2s;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 32px; /* Larger thumb */
            height: 32px;
            background: #42a5f5; /* New vibrant blue accent */
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(0,0,0,0.6), 0 0 20px rgba(66, 165, 245, 1); /* Stronger glow */
        }

        input[type="range"]::-moz-range-thumb {
            width: 32px;
            height: 32px;
            background: #42a5f5; /* New vibrant blue accent */
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(0,0,0,0.6), 0 0 20px rgba(66, 165, 245, 1);
        }

        .info-title { /* Used for modal titles and Apps Menu Page H2 */
            @apply text-4xl font-extrabold text-center mb-8; /* Larger, bolder title */
            color: #42a5f5;
            text-shadow: 0 0 10px rgba(66, 165, 245, 0.6);
        }

        .info-body {
            @apply text-lg text-gray-200 leading-relaxed;
        }

        /* Styling for the small language buttons */
        .lang-button {
            @apply text-sm px-2 py-1 rounded-md transition-all duration-200 ease-in-out;
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #e0e7eb;
        }
        .lang-button:hover {
            background-color: rgba(255, 255, 255, 0.15);
            transform: scale(1.05);
        }
        .lang-button.active {
            background: linear-gradient(145deg, #42a5f5, #2196f3);
            border-color: #42a5f5;
            color: #fff;
            font-weight: 600;
            text-shadow: 0 0 5px rgba(66, 165, 245, 0.8);
        }


    </style>
</head>
<body class="h-screen w-screen flex items-center justify-center hmi-background text-white">

    <div id="hmi-container" class="relative z-10 p-8 w-full h-full flex flex-col display-frame"> {# Added display-frame class #}

        <div class="flex justify-between items-center text-gray-400 text-base mb-3 px-3"> {# Slightly larger font, more padding #}
            <div id="currentTime" class="font-medium"></div>
            <div class="flex items-center space-x-3"> {# Slightly more space #}
                <i class="fas fa-wifi"></i>
                <i id="batteryIcon" class="fas fa-battery-full"></i>
                <span id="batteryValue"></span>
                <span id="tempDisplay"></span>
                {# Language Switch Buttons #}
                <button id="langEnButton" class="lang-button">EN</button>
                <button id="langDeButton" class="lang-button">DE</button>
            </div>
        </div>

        <div class="flex justify-between items-center text-gray-300 px-6 py-4 mb-8 dashboard-card"> {# Increased padding/margin #}
            <div class="flex items-center text-xl font-medium">
                <i class="fas fa-compass mr-3 text-[#00bcd4]"></i>
                <span data-lang-key="top_bar_navigation">Navigation</span>
            </div>
            <div class="flex items-center text-3xl font-extrabold text-[#42a5f5] tracking-wide animate-pulse-subtle"> {# Larger, bolder text, added pulse animation #}
                <span data-lang-key="top_bar_autonomous_driving">AUTONOMOUS DRIVING</span>
            </div>
            <div class="text-xl flex items-center"> {# Larger font #}
                <i class="fas fa-music mr-2 text-gray-400"></i>
                <span data-lang-key="top_bar_now_playing">Now Playing</span>
            </div>
        </div>

        <div class="flex-grow grid grid-cols-3 gap-8 mb-8"> {# Increased gap #}
            <div class="col-span-2 dashboard-card flex flex-col items-center justify-center relative overflow-hidden p-0">
                <h3 class="text-2xl font-semibold mb-4 text-gray-300 absolute top-8 left-8 z-10" data-lang-key="map_current_location">Current Location</h3> {# Larger heading #}
                <div class="w-full h-full bg-blue-950 flex items-center justify-center text-gray-400 text-6xl relative overflow-hidden">
                    <i class="fas fa-map-marked-alt opacity-20 text-gray-600 absolute animate-pulse"></i>
                    <div class="w-48 h-48 bg-sky-500 rounded-full flex items-center justify-center absolute -bottom-24 -right-24 opacity-15 filter blur-3xl animate-blob-slow"></div> {# Larger blobs #}
                    <div class="w-40 h-40 bg-teal-500 rounded-full flex items-center justify-center absolute -top-20 -left-20 opacity-15 filter blur-3xl animate-blob-fast"></div> {# Larger blobs #}
                    <div class="absolute inset-0 flex items-center justify-center">
                        <i class="fas fa-map-marker-alt text-[#00bcd4] text-8xl animate-bounce-subtle"></i> {# Larger icon #}
                    </div>
                    <div class="absolute bottom-8 left-8 text-2xl font-semibold text-gray-300 flex items-center z-10"> {# Larger font #}
                        <i class="fas fa-car mr-3 text-[#42a5f5]"></i>
                        <span data-lang-key="driving_status">DRIVING</span>
                    </div>
                </div>
            </div>

            <div class="col-span-1 flex flex-col gap-8"> {# Increased gap #}
                <div class="dashboard-card flex flex-col items-center justify-center flex-grow">
                    <p class="text-9xl font-extrabold text-[#00bcd4]">70</p> {# Larger, bolder speed #}
                    <p class="text-4xl font-semibold text-gray-300">km/h</p> {# Larger km/h #}
                </div>
                <div class="dashboard-card flex flex-col items-center justify-center flex-grow">
                    <p class="text-2xl font-semibold text-gray-300 mb-2" data-lang-key="arrival_label">Arrival</p> {# Larger arrival label #}
                    <p class="text-6xl font-bold text-[#42a5f5]" id="arrivalTimeDisplay">11:45</p> {# Larger arrival time #}
                </div>
                <div class="dashboard-card flex flex-col items-center justify-center flex-grow">
                    <p class="text-7xl text-yellow-400 mb-2"><i class="fas fa-sun"></i></p> {# Larger icon #}
                    <p class="text-6xl font-bold text-white">21°</p> {# Larger temp #}
                    <p class="text-2xl font-semibold text-gray-300" data-lang-key="weather_sunny">Sunny</p> {# Larger weather description #}
                </div>
            </div>
        </div>

        <div class="grid grid-cols-3 gap-8 pt-4"> {# Changed to grid-cols-3 #}
            <button id="appsButton" class="hmi-button" data-target-route="apps_menu">
                <i class="hmi-button-icon fas fa-th-large"></i>
                <span class="hmi-button-text" data-lang-key="apps_button">Apps</span>
            </button>

            <button id="systemPreferencesButtonDashboard" class="hmi-button"> {# Renamed ID to avoid conflict #}
                <i class="hmi-button-icon fas fa-sliders-h"></i>
                <span class="hmi-button-text" data-lang-key="settings_button">Settings</span>
            </button>

            <button id="phoneButton" class="hmi-button">
                <i class="hmi-button-icon fas fa-phone"></i>
                <span class="hmi-button-text" data-lang-key="phone_button">Phone</span>
            </button>
        </div>

    </div>

    <div id="systemPreferencesModal" class="modal-overlay hidden opacity-0">
        <div class="modal-content">
            <button id="closeSystemPreferencesModal" class="modal-close-button">&times;</button>
            <h2 class="info-title" data-lang-key="system_preferences_title">System Preferences</h2>

            <div class="mb-6">
                <label for="brightnessSlider" class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="brightness_label">Brightness: <span id="brightnessValue">100</span>%</label>
                <input type="range" id="brightnessSlider" min="50" max="150" value="100" class="w-full">
            </div>

            <div class="mb-6">
                <span class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="language_label">Language:</span>
                <div class="flex space-x-4">
                    <button id="langEnButtonModal" class="hmi-button py-2 px-4 text-base">English</button> {# ID changed for modal button #}
                    <button id="langDeButtonModal" class="hmi-button py-2 px-4 text-base">Deutsch</button> {# ID changed for modal button #}
                </div>
            </div>

            <div class="mb-4">
                <p class="text-lg text-gray-200"><strong data-lang-key="display_setting">Display:</strong> <span data-lang-key="auto_brightness">Auto Brightness (On)</span></p>
            </div>
            <div class="mb-4">
                <p class="text-lg text-gray-200"><strong data-lang-key="audio_setting">Audio:</strong> <span data-lang-key="voice_prompts">Voice Prompts (On)</span></p>
            </div>
            <div class="mb-4">
                <p class="text-lg text-gray-200"><strong data-lang-key="connectivity_setting">Connectivity:</strong> <span data-lang-key="5g_active">5G Active</span></p>
            </div>
        </div>
    </div>

    <audio id="clickSound" preload="auto">
        <source src="/static/sounds/click.mp3" type="audio/mpeg">
        <source src="/static/sounds/click.wav" type="audio/wav">
        Your browser does not support the audio element.
    </audio>

    <script>
        // Get elements specific to the Dashboard page
        const hmiContainer = document.getElementById('hmi-container'); // Main container for brightness filter
        const currentTimeSpan = document.getElementById('currentTime');
        const batteryIcon = document.getElementById('batteryIcon');
        const batteryValueSpan = document.getElementById('batteryValue');
        const tempDisplaySpan = document.getElementById('tempDisplay');
        const arrivalTimeDisplay = document.getElementById('arrivalTimeDisplay'); // For arrival time on dashboard

        // Main Dashboard buttons (Apps and Phone)
        const appsButton = document.getElementById('appsButton'); // The "Apps" button on dashboard
        const phoneButton = document.getElementById('phoneButton'); // Phone button on dashboard
        const systemPreferencesButtonDashboard = document.getElementById('systemPreferencesButtonDashboard'); // Dashboard Settings button

        // Language Buttons on Dashboard Top Bar
        const langEnButton = document.getElementById('langEnButton'); // EN button on dashboard top bar
        const langDeButton = document.getElementById('langDeButton'); // DE button on dashboard top bar

        // System Preferences Modal elements (now on Dashboard page)
        const systemPreferencesModal = document.getElementById('systemPreferencesModal');
        const closeSystemPreferencesModal = document.getElementById('closeSystemPreferencesModal');
        const brightnessSlider = document.getElementById('brightnessSlider');
        const brightnessValueSpan = document.getElementById('brightnessValue');
        // Language Buttons INSIDE System Preferences Modal
        const langEnButtonModal = document.getElementById('langEnButtonModal');
        const langDeButtonModal = document.getElementById('langDeButtonModal');


        const clickSound = document.getElementById('clickSound');

        // Function to play click sound
        function playClickSound() {
            if (clickSound) {
                clickSound.currentTime = 0; // Reset to start for quick successive clicks
                clickSound.play().catch(e => console.log("Sound play interrupted or failed:", e));
            }
        }

        // --- Language Management ---
        let currentLanguage = 'en'; // Default language, will be updated on DOMContentLoaded

        const translations = {
            'en': {
                title: 'Autonomous Shuttle HMI',
                top_bar_navigation: 'Navigation',
                top_bar_autonomous_driving: 'AUTONOMOUS DRIVING',
                top_bar_now_playing: 'Now Playing',
                map_current_location: 'Current Location',
                driving_status: 'DRIVING',
                arrival_label: 'Arrival',
                weather_sunny: 'Sunny',
                video_button: 'Video',
                apps_button: 'Apps',
                settings_button: 'Settings',
                phone_button: 'Phone',
                apps_menu_title: 'Applications', // NEW Translation for Apps modal title

                // Original Tile Menu Translations (reused for Apps Modal)
                route_button_text: 'Route & Destination',
                shuttle_status_button_text: 'Shuttle Status',
                entertainment_button_text: 'Entertainment',
                emergency_button_text: 'Emergency Assist',
                hvac_button_text: 'HVAC Settings',
                entry_exit_button_text: 'Entry/Exit',
                interior_comfort_button_text: 'Interior Comfort',
                system_preferences_button_text: 'System Preferences',

                // Modal/Info Page translations
                hvac_title: 'HVAC Controls',
                temperature_label: 'Temperature:',
                fan_speed_label: 'Fan Speed:',
                ac_label: 'A/C',
                airflow_label: 'Airflow Direction:',
                face_button: 'Face',
                feet_button: 'Feet',
                defrost_button: 'Defrost',
                sync_climate_button_text: 'Sync Climate',
                system_preferences_title: 'System Preferences',
                brightness_label: 'Brightness:',
                language_label: 'Language:',
                display_setting: 'Display:',
                auto_brightness: 'Auto Brightness (On)',
                audio_setting: 'Audio:',
                voice_prompts: 'Voice Prompts (On)',
                connectivity_setting: 'Connectivity:',
                '5g_active': '5G Active',
                lock_status_locked: 'Locked',
                lock_status_unlocked: 'Unlocked',
                volume_status: 'Volume: ',
                phone_status_calling: 'Calling...',
                phone_status_idle: 'Call',
                back_to_home_menu: 'Back to Home', // Added for new apps page
                back_to_apps_menu: 'Back to Apps Menu', // Added for info pages
            },
            'de': {
                title: 'Autonomes Shuttle HMI',
                top_bar_navigation: 'Navigation',
                top_bar_autonomous_driving: 'AUTONOMES FAHREN',
                top_bar_now_playing: 'Aktuelle Wiedergabe',
                map_current_location: 'Aktueller Standort',
                driving_status: 'FÄHRT',
                arrival_label: 'Ankunft',
                weather_sunny: 'Sonnig',
                video_button: 'Video',
                apps_button: 'Apps',
                settings_button: 'Einstellungen',
                phone_button: 'Telefon',
                apps_menu_title: 'Anwendungen', // NEW Translation for Apps modal title

                // Original Tile Menu Translations (reused for Apps Modal)
                route_button_text: 'Route & Ziel',
                shuttle_status_button_text: 'Shuttle Status',
                entertainment_button_text: 'Unterhaltung',
                emergency_button_text: 'Notfallhilfe',
                hvac_button_text: 'Klima-Einstellungen',
                entry_exit_button_text: 'Ein-/Ausstieg',
                interior_comfort_button_text: 'Innenraumkomfort',
                system_preferences_button_text: 'Systemeinstellungen',

                // Modal/Info Page translations
                hvac_title: 'Klima-Steuerung',
                temperature_label: 'Temperatur:',
                fan_speed_label: 'Lüftergeschwindigkeit:',
                ac_label: 'Klimaanlage',
                airflow_label: 'Luftstromrichtung:',
                face_button: 'Gesicht',
                feet_button: 'Füße',
                defrost_button: 'Enteisen',
                sync_climate_button_text: 'Klima synchronisieren',
                system_preferences_title: 'Systemeinstellungen',
                brightness_label: 'Helligkeit:',
                language_label: 'Sprache:',
                display_setting: 'Anzeige:',
                auto_brightness: 'Automatische Helligkeit (Ein)',
                audio_setting: 'Audio:',
                voice_prompts: 'Sprachansagen (Ein)',
                connectivity_setting: 'Konnektivität:',
                '5g_active': '5G Aktiv',
                lock_status_locked: 'Gesperrt',
                lock_status_unlocked: 'Entsperrt',
                volume_status: 'Lautstärke: ',
                phone_status_calling: 'Anruf läuft...',
                phone_status_idle: 'Anruf',
                back_to_home_menu: 'Zurück zum Hauptmenü', // Added for new apps page
                back_to_apps_menu: 'Zurück zum Apps-Menü', // Added for info pages
            }
        };

        function updateLanguage(lang) {
            currentLanguage = lang;
            localStorage.setItem('hmiLanguage', lang); // Persist language choice

            // Update main page title
            document.querySelector('title').textContent = translations[currentLanguage]['title'];

            // Update all elements with data-lang-key on the current page
            document.querySelectorAll('[data-lang-key]').forEach(element => {
                const key = element.getAttribute('data-lang-key');
                if (translations[currentLanguage][key]) {
                    element.textContent = translations[currentLanguage][key];
                }
            });

            // Update active state for dashboard language buttons
            if (langEnButton) langEnButton.classList.remove('active');
            if (langDeButton) langDeButton.classList.remove('active');
            if (lang === 'en' && langEnButton) langEnButton.classList.add('active');
            if (lang === 'de' && langDeButton) langDeButton.classList.add('active');

            // Update modal titles (if modal is present on this page)
            const systemPreferencesTitleElement = document.querySelector('#systemPreferencesModal .info-title');
            if (systemPreferencesTitleElement && translations[currentLanguage]['system_preferences_title']) {
                systemPreferencesTitleElement.textContent = translations[currentLanguage]['system_preferences_title'];
            }

            // Re-render System Preferences modal content if it's open
            if (systemPreferencesModal && !systemPreferencesModal.classList.contains('hidden')) {
                document.querySelector('#systemPreferencesModal label[data-lang-key="brightness_label"] span').textContent = translations[currentLanguage]['brightness_label'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="language_label"]').textContent = translations[currentLanguage]['language_label'];
                document.querySelector('#systemPreferencesModal p strong[data-lang-key="display_setting"]').textContent = translations[currentLanguage]['display_setting'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="auto_brightness"]').textContent = translations[currentLanguage]['auto_brightness'];
                document.querySelector('#systemPreferencesModal p strong[data-lang-key="audio_setting"]').textContent = translations[currentLanguage]['audio_setting'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="voice_prompts"]').textContent = translations[currentLanguage]['voice_prompts'];
                document.querySelector('#systemPreferencesModal p strong[data-lang-key="connectivity_setting"]').textContent = translations[currentLanguage]['connectivity_setting'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="5g_active"]').textContent = translations[currentLanguage]['5g_active'];
            }
        }

        // --- Generic Modal Functions ---
        function showModal(modalElement) {
            modalElement.classList.remove('hidden');
            setTimeout(() => {
                modalElement.classList.remove('opacity-0');
            }, 10);
        }
        function hideModal(modalElement) {
            modalElement.classList.add('opacity-0');
            setTimeout(() => {
                modalElement.classList.add('hidden');
            }, 300);
        }

        // --- Event Listeners specific to Dashboard ---

        // Dashboard buttons that navigate to new Flask routes (only 'Apps' now)
        if (appsButton) {
            appsButton.addEventListener('click', () => {
                playClickSound();
                window.location.href = `/apps_menu?lang=${currentLanguage}`; // Pass language via URL param
            });
        }

        // Dashboard Settings button (opens modal directly from dashboard)
        if (systemPreferencesButtonDashboard) {
            systemPreferencesButtonDashboard.addEventListener('click', () => {
                playClickSound();
                showModal(systemPreferencesModal);
            });
        }
        if (closeSystemPreferencesModal) {
            closeSystemPreferencesModal.addEventListener('click', () => {
                playClickSound();
                hideModal(systemPreferencesModal);
            });
        }
        if (systemPreferencesModal) {
            systemPreferencesModal.addEventListener('click', (event) => {
                if (event.target === systemPreferencesModal) {
                    playClickSound();
                    hideModal(systemPreferencesModal);
                }
            });
        }

        // Brightness Control (within Dashboard's System Preferences modal)
        if (brightnessSlider) {
            brightnessSlider.addEventListener('input', (event) => {
                const brightness = event.target.value;
                brightnessValueSpan.textContent = brightness;
                hmiContainer.style.filter = `brightness(${brightness}%)`; // Affects main dashboard container
            });
        }
        // Language Selection (within Dashboard's System Preferences modal)
        if (langEnButtonModal) { // Using the specific modal button ID
            langEnButtonModal.addEventListener('click', () => {
                playClickSound();
                updateLanguage('en'); // Updates language on the dashboard page and persists
            });
        }
        if (langDeButtonModal) { // Using the specific modal button ID
            langDeButtonModal.addEventListener('click', () => {
                playClickSound();
                updateLanguage('de'); // Updates language on the dashboard page and persists
            });
        }

        // Language buttons on the Dashboard top bar
        if (langEnButton) {
            langEnButton.addEventListener('click', () => {
                playClickSound();
                updateLanguage('en');
            });
        }
        if (langDeButton) {
            langDeButton.addEventListener('click', () => {
                playClickSound();
                updateLanguage('de');
            });
        }


        // Phone button click logic (from dashboard bottom bar)
        if (phoneButton) {
            let isCalling = false;
            phoneButton.addEventListener('click', () => {
                playClickSound();
                isCalling = !isCalling;
                const phoneIcon = phoneButton.querySelector('i');
                const phoneText = phoneButton.querySelector('.hmi-button-text');
                if (isCalling) {
                    phoneIcon.classList.remove('fa-phone');
                    phoneIcon.classList.add('fa-phone-volume');
                    if (phoneText) phoneText.textContent = translations[currentLanguage]['phone_status_calling'];
                    console.log(translations[currentLanguage]['phone_status_calling']);
                } else {
                    phoneIcon.classList.remove('fa-phone-volume');
                    phoneIcon.classList.add('fa-phone');
                    if (phoneText) phoneText.textContent = translations[currentLanguage]['phone_status_idle'];
                    console.log(translations[currentLanguage]['phone_status_idle']);
                }
            });
        }


        // --- Header Live Updates (Time, Battery, Temperature) and Arrival Time ---
        function updateHeaderInfo() {
            const now = new Date();
            const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            currentTimeSpan.textContent = timeString;

            const arrivalTime = new Date(now.getTime() + (Math.floor(Math.random() * 10) + 10) * 60000);
            arrivalTimeDisplay.textContent = arrivalTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            let batteryLevel = parseInt(batteryValueSpan.textContent) || 100;
            if (Math.random() > 0.7) {
                batteryLevel += (Math.random() > 0.5 ? 1 : -1) * Math.floor(Math.random() * 3);
                if (batteryLevel > 100) batteryLevel = 100;
                if (batteryLevel < 0) batteryLevel = 0;
            }
            batteryValueSpan.textContent = `${batteryLevel}%`;

            batteryIcon.classList.remove('fa-battery-full', 'fa-battery-three-quarters', 'fa-battery-half', 'fa-battery-quarter', 'fa-battery-empty');
            if (batteryLevel > 75) {
                batteryIcon.classList.add('fa-battery-full');
            } else if (batteryLevel > 50) {
                batteryIcon.classList.add('fa-battery-three-quarters');
            } else if (batteryLevel > 25) {
                batteryIcon.classList.add('fa-battery-half');
            } else if (batteryLevel > 10) {
                batteryIcon.classList.add('fa-battery-quarter');
            } else {
                batteryIcon.classList.add('fa-battery-empty');
                batteryIcon.style.color = 'red';
            }

            let currentTempC = parseFloat(tempDisplaySpan.textContent) || 21;
            if (Math.random() > 0.8) {
                currentTempC += (Math.random() > 0.5 ? 0.5 : -0.5);
                if (currentTempC > 28) currentTempC = 28;
                if (currentTempC < 18) currentTempC = 18;
            }
            tempDisplaySpan.textContent = `${currentTempC.toFixed(0)}°C`;
        }

        document.addEventListener('DOMContentLoaded', () => {
            // Priority: 1. localStorage, 2. URL param, 3. default 'en'
            const savedLang = localStorage.getItem('hmiLanguage');
            const urlLang = new URLSearchParams(window.location.search).get('lang');
            currentLanguage = savedLang || urlLang || 'en'; // Set initial language
            updateLanguage(currentLanguage); // Apply initial language to page elements
            updateHeaderInfo(); // Initial header update
            setInterval(updateHeaderInfo, 5000); // Update header every 5 seconds
        });

    </script>
</body>
</html>
"""

# --- HTML Content for the Apps Menu Page ---
APPS_MENU_HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-lang-key="apps_menu_title">Applications</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        body {
            font-family: 'Inter', sans-serif;
            overflow: hidden; /* Prevent scrolling */
        }

        /* Common style for the main display frame on both Dashboard and Apps Menu */
        .display-frame {
            transition: filter 0.3s ease-in-out;
            width: 100vw; /* Take full viewport width */
            height: 100vh; /* Take full viewport height */
            max-width: 1280px; /* Max width for larger displays, maintains proportions */
            max-height: 800px; /* Adjust height to maintain a consistent aspect ratio (e.g., 16:10 or 16:9 on common tablets) */
            border-radius: 2.5rem; /* More rounded corners for the whole interface */
            overflow: hidden; /* Ensure content stays within rounded corners */
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 40px 80px rgba(0, 0, 0, 0.5); /* Deeper main shadow */
        }

        /* Custom gradient background for the whole HMI - applied to body for consistent environment */
        .hmi-background {
            background: linear-gradient(135deg, #101c2a 0%, #1c2a3b 100%); /* Even deeper, richer blue-gray gradient */
            position: relative;
            overflow: hidden;
            background-size: 400% 400%;
            animation: gradient-animation 25s ease infinite;
        }

        @keyframes gradient-animation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Dynamic animated glowing dots/particles - applied to body for consistent environment */
        .hmi-background::before,
        .hmi-background::after {
            content: '';
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            filter: blur(80px); /* Increased blur for softer glow */
            opacity: 0.20; /* Slightly less opaque for subtler effect */
        }

        .hmi-background::before {
            width: 350px; /* Larger */
            height: 350px;
            background: #2196f3; /* Stronger blue glow */
            top: 10%; /* Adjusted position */
            left: 5%;
            animation: glow-move-one 25s infinite alternate ease-in-out; /* Slightly different animation speed */
        }

        .hmi-background::after {
            width: 300px; /* Larger */
            height: 300px;
            background: #00e5ff; /* Brighter teal glow for connectivity */
            bottom: 8%; /* Adjusted position */
            right: 5%;
            animation: glow-move-two 30s infinite alternate-reverse ease-in-out; /* Slightly different animation speed */
        }

        @keyframes glow-move-one {
            0% { transform: translate(0, 0); }
            50% { transform: translate(60vw, 40vh); }
            100% { transform: translate(0, 0); }
        }

        @keyframes glow-move-two {
            0% { transform: translate(0, 0); }
            50% { transform: translate(-50vw, -30vh); }
            100% { transform: translate(0, 0); }
        }

        /* Card/Widget styling for dashboard elements - Deeper inset and subtle highlight */
        .dashboard-card {
            @apply bg-gray-900 p-6 rounded-2xl shadow-inner border border-gray-700 relative; /* Darker base, shadow-inner for recessed feel */
            background: linear-gradient(160deg, #2a3d50, #1a242f); /* Darker and more contrasted gradient */
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6), /* Inset dark shadow */
                        inset 0 -2px 4px rgba(255, 255, 255, 0.05), /* Subtle inset highlight */
                        0 8px 15px rgba(0, 0, 0, 0.4); /* Outer floating shadow */
            transition: all 0.2s ease-in-out;
        }
        .dashboard-card:hover {
            transform: translateY(-2px); /* Slight lift on hover */
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.7),
                        inset 0 -2px 4px rgba(255, 255, 255, 0.08),
                        0 12px 25px rgba(0, 0, 0, 0.6);
        }

        /* Button styling for bottom row - adapted for icon-text side-by-side */
        .hmi-button {
            @apply relative flex items-center justify-center p-4 rounded-xl shadow-lg transition-all duration-300 ease-in-out transform;
            background: linear-gradient(145deg, #374151, #1f2937); /* Keep dark neutral base */
            border: 1px solid rgba(255, 255, 255, 0.12); /* Slightly stronger border */
            color: #e0e7eb; /* Slightly brighter text color */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2),
                        0 10px 20px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.08); /* Stronger inner highlight */
            flex-direction: row; /* Default for bottom buttons */
        }

        /* Specific hmi-button adjustments for the Apps Menu page */
        .apps-menu-container .hmi-button { /* Target buttons ONLY within the apps menu container */
            flex-direction: column; /* Back to column for tile menu */
            min-height: 150px; /* Ensure buttons have enough space */
        }
        .apps-menu-container .hmi-button-icon { /* Target icons ONLY within the apps menu container */
            @apply text-5xl mr-0 mb-3; /* Larger icon for tile menu, no right margin, add bottom margin */
        }
        .apps-menu-container .hmi-button-text { /* Target text ONLY within the apps menu container */
            @apply text-xl;
        }


        .hmi-button:hover {
            transform: translateY(-3px) scale(1.06); /* More pronounced lift and scale */
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.35),
                        0 15px 30px rgba(0, 0, 0, 0.45),
                        inset 0 1px 0 rgba(255, 255, 255, 0.15); /* Stronger hover highlight */
            @apply focus:outline-none focus:ring-4 focus:ring-[#42a5f5] focus:ring-opacity-70; /* Slightly more opaque ring */
        }

        .hmi-button:active {
            transform: scale(0.97); /* Slightly more compression */
            box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.6), /* Deeper inset on press */
                        inset 0 -1px 2px rgba(255, 255, 255, 0.05);
        }

        .hmi-button-icon {
            @apply text-3xl mr-3; /* Adjusted size and margin for horizontal layout */
            color: #42a5f5; /* New vibrant blue accent */
            text-shadow: 0 0 15px rgba(66, 165, 245, 0.9); /* Stronger icon glow */
        }

        .hmi-button-text {
            @apply text-xl font-semibold;
            text-shadow: 0 0 8px rgba(224, 231, 235, 0.5); /* Stronger text glow */
        }

        /* Specific emergency button style */
        .hmi-button.emergency {
            background: linear-gradient(145deg, #dc2626, #b91c1c); /* Red gradient */
            color: #fff;
        }
        .hmi-button.emergency .hmi-button-icon {
            color: #fff;
            text-shadow: 0 0 15px rgba(220, 38, 38, 0.9); /* Stronger red glow */
        }

        /* Map Placeholder Animations */
        @keyframes blob-slow {
            0%, 100% { transform: translate(0, 0) scale(1); }
            30% { transform: translate(20%, 10%) scale(1.2); }
            60% { transform: translate(-10%, 20%) scale(0.9); }
            80% { transform: translate(15%, -5%) scale(1.1); }
        }

        @keyframes blob-fast {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25% { transform: translate(-15%, -10%) scale(1.1); }
            50% { transform: translate(5%, 15%) scale(0.8); }
            75% { transform: translate(10%, -10%) scale(1.2); }
        }

        @keyframes bounce-subtle {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); /* More pronounced bounce */ }
        }


        /* Modal/Overlay styling for HVAC, System Preferences */
        .modal-overlay {
            @apply fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 transition-opacity duration-300 ease-in-out; /* Darker overlay */
        }

        .modal-content {
            @apply bg-gray-800 p-10 rounded-3xl shadow-2xl w-full max-w-lg mx-4 border border-gray-700 relative;
            background: linear-gradient(160deg, #2a3d50, #1c2a3b); /* Consistent with new background */
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4),
                        0 20px 40px rgba(0, 0, 0, 0.5),
                        inset 0 2px 0 rgba(255, 255, 255, 0.1); /* Stronger inner highlight */
        }

        .modal-close-button {
            @apply absolute top-5 right-5 text-gray-400 hover:text-white text-4xl focus:outline-none;
        }

        /* Slider styling with glow - updated accent color */
        input[type="range"] {
            -webkit-appearance: none;
            width: 100%;
            height: 12px; /* Slightly thicker slider */
            background: #4a5568;
            border-radius: 6px;
            outline: none;
            transition: opacity .2s;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 32px; /* Larger thumb */
            height: 32px;
            background: #42a5f5; /* New vibrant blue accent */
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(0,0,0,0.6), 0 0 20px rgba(66, 165, 245, 1); /* Stronger glow */
        }

        input[type="range"]::-moz-range-thumb {
            width: 32px;
            height: 32px;
            background: #42a5f5; /* New vibrant blue accent */
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(0,0,0,0.6), 0 0 20px rgba(66, 165, 245, 1);
        }

        .info-title { /* Used for modal titles and Apps Menu Page H2 */
            @apply text-4xl font-extrabold text-center mb-8; /* Larger, bolder title */
            color: #42a5f5;
            text-shadow: 0 0 10px rgba(66, 165, 245, 0.6);
        }

        .info-body {
            @apply text-lg text-gray-200 leading-relaxed;
        }

        /* Styling for the small language buttons */
        .lang-button {
            @apply text-sm px-2 py-1 rounded-md transition-all duration-200 ease-in-out;
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #e0e7eb;
        }
        .lang-button:hover {
            background-color: rgba(255, 255, 255, 0.15);
            transform: scale(1.05);
        }
        .lang-button.active {
            background: linear-gradient(145deg, #42a5f5, #2196f3);
            border-color: #42a5f5;
            color: #fff;
            font-weight: 600;
            text-shadow: 0 0 5px rgba(66, 165, 245, 0.8);
        }


    </style>
</head>
<body class="h-screen w-screen flex items-center justify-center hmi-background text-white">

    <div id="apps-menu-container" class="relative z-10 p-8 w-full h-full flex flex-col display-frame"> {# Main container for Apps Menu Page, now uses display-frame #}

        <div class="flex justify-between items-center text-gray-400 text-base mb-3 px-3">
            <div id="currentTime" class="font-medium"></div>
            <div class="flex items-center space-x-3">
                <i class="fas fa-wifi"></i>
                <i id="batteryIcon" class="fas fa-battery-full"></i>
                <span id="batteryValue"></span>
                <span id="tempDisplay"></span>
                {# Language Switch Buttons - on Apps Menu #}
                <button id="langEnButtonAppsMenu" class="lang-button">EN</button>
                <button id="langDeButtonAppsMenu" class="lang-button">DE</button>
            </div>
        </div>

        <h2 class="info-title" data-lang-key="apps_menu_title">Applications</h2>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 flex-grow p-4"> {# Added padding here #}
            <button class="hmi-button" data-target-route="route">
                <i class="hmi-button-icon fas fa-route"></i>
                <span class="hmi-button-text" data-lang-key="route_button_text">Route & Destination</span>
            </button>

            <button class="hmi-button" data-target-route="shuttle_status">
                <i class="hmi-button-icon fas fa-bus"></i>
                <span class="hmi-button-text" data-lang-key="shuttle_status_button_text">Shuttle Status</span>
            </button>

            <button class="hmi-button" data-target-route="entertainment">
                <i class="hmi-button-icon fas fa-film"></i>
                <span class="hmi-button-text" data-lang-key="entertainment_button_text">Entertainment</span>
            </button>

            <button class="hmi-button emergency" data-target-route="emergency">
                <i class="hmi-button-icon fas fa-life-ring text-white"></i>
                <span class="hmi-button-text text-white" data-lang-key="emergency_button_text">Emergency Assist</span>
            </button>

            <button id="hvacButtonAppsMenu" class="hmi-button">
                <i class="hmi-button-icon fas fa-fan"></i>
                <span class="hmi-button-text" data-lang-key="hvac_button_text">HVAC Settings</span>
            </button>

            <button class="hmi-button" data-target-route="entry_exit">
                <i class="hmi-button-icon fas fa-door-closed"></i>
                <span class="hmi-button-text" data-lang-key="entry_exit_button_text">Entry/Exit</span>
            </button>

            <button class="hmi-button" data-target-route="interior_comfort">
                <i class="hmi-button-icon fas fa-couch"></i>
                <span class="hmi-button-text" data-lang-key="interior_comfort_button_text">Interior Comfort</span>
            </button>

            <button id="systemPreferencesButtonAppsMenu" class="hmi-button">
                <i class="hmi-button-icon fas fa-sliders-h"></i>
                <span class="hmi-button-text" data-lang-key="system_preferences_button_text">System Preferences</span>
            </button>
        </div>

        <div class="mt-8 flex justify-center">
            <a href="/" class="back-button">
                <i class="back-button-icon fas fa-arrow-left"></i>
                <span class="back-button-text" data-lang-key="back_to_home_menu">Back to Home</span>
            </a>
        </div>
    </div>

    <div id="hvacModal" class="modal-overlay hidden opacity-0">
        <div class="modal-content">
            <button id="closeHvacModal" class="modal-close-button">&times;</button>
            <h2 class="info-title" style="color: #42a5f5;" data-lang-key="hvac_title">HVAC Controls</h2>

            <div class="mb-6">
                <label for="temperature" class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="temperature_label">Temperature: <span id="tempValue">22</span>°C</label>
                <input type="range" id="temperature" min="18" max="28" value="22" class="w-full">
            </div>

            <div class="mb-6">
                <label for="fanSpeed" class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="fan_speed_label">Fan Speed: <span id="fanValue">3</span></label>
                <input type="range" id="fanSpeed" min="1" max="5" value="3" class="w-full">
            </div>

            <div class="flex items-center justify-between mb-6">
                <span class="text-xl font-semibold text-gray-300" data-lang-key="ac_label">A/C</span>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" value="" class="sr-only peer" checked>
                    <div class="w-14 h-8 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#42a5f5] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-[#42a5f5]"></div>
                </label>
            </div>

            <div class="mb-6">
                <span class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="airflow_label">Airflow Direction:</span>
                <div class="grid grid-cols-3 gap-4">
                    <button class="hmi-button py-2 px-4 text-sm" data-lang-key="face_button">Face</button>
                    <button class="hmi-button py-2 px-4 text-sm" data-lang-key="feet_button">Feet</button>
                    <button class="hmi-button py-2 px-4 text-sm" data-lang-key="defrost_button">Defrost</button>
                </div>
            </div>

            <button class="w-full hmi-button py-3 text-xl font-bold mt-4" style="background: linear-gradient(145deg, #42a5f5, #2196f3);" data-lang-key="sync_climate_button">
                <i class="fas fa-sync-alt mr-2"></i> <span data-lang-key="sync_climate_button_text">Sync Climate</span>
            </button>
        </div>
    </div>

    <div id="systemPreferencesModal" class="modal-overlay hidden opacity-0">
        <div class="modal-content">
            <button id="closeSystemPreferencesModal" class="modal-close-button">&times;</button>
            <h2 class="info-title" data-lang-key="system_preferences_title">System Preferences</h2>

            <div class="mb-6">
                <label for="brightnessSlider" class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="brightness_label">Brightness: <span id="brightnessValue">100</span>%</label>
                <input type="range" id="brightnessSlider" min="50" max="150" value="100" class="w-full">
            </div>

            <div class="mb-6">
                <span class="block text-xl font-semibold mb-3 text-gray-300" data-lang-key="language_label">Language:</span>
                <div class="flex space-x-4">
                    <button id="langEnButtonModalApps" class="hmi-button py-2 px-4 text-base">English</button> {# ID changed for modal button on apps menu #}
                    <button id="langDeButtonModalApps" class="hmi-button py-2 px-4 text-base">Deutsch</button> {# ID changed for modal button on apps menu #}
                </div>
            </div>

            <div class="mb-4">
                <p class="text-lg text-gray-200"><strong data-lang-key="display_setting">Display:</strong> <span data-lang-key="auto_brightness">Auto Brightness (On)</span></p>
            </div>
            <div class="mb-4">
                <p class="text-lg text-gray-200"><strong data-lang-key="audio_setting">Audio:</strong> <span data-lang-key="voice_prompts">Voice Prompts (On)</span></p>
            </div>
            <div class="mb-4">
                <p class="text-lg text-gray-200"><strong data-lang-key="connectivity_setting">Connectivity:</strong> <span data-lang-key="5g_active">5G Active</span></p>
            </div>
        </div>
    </div>

    <audio id="clickSound" preload="auto">
        <source src="/static/sounds/click.mp3" type="audio/mpeg">
        <source src="/static/sounds/click.wav" type="audio/wav">
        Your browser does not support the audio element.
    </audio>

    <script>
        // Get elements specific to the Apps Menu page
        const appsMenuContainer = document.getElementById('apps-menu-container'); // Get the main container for apps menu
        const currentTimeSpan = document.getElementById('currentTime');
        const batteryIcon = document.getElementById('batteryIcon');
        const batteryValueSpan = document.getElementById('batteryValue');
        const tempDisplaySpan = document.getElementById('tempDisplay');

        // Language Buttons on Apps Menu Top Bar
        const langEnButtonAppsMenu = document.getElementById('langEnButtonAppsMenu'); // EN button on Apps Menu top bar
        const langDeButtonAppsMenu = document.getElementById('langDeButtonAppsMenu'); // DE button on Apps Menu top bar

        // Modals elements present on this page
        const hvacModal = document.getElementById('hvacModal');
        const closeHvacModal = document.getElementById('closeHvacModal');
        const systemPreferencesModal = document.getElementById('systemPreferencesModal');
        const closeSystemPreferencesModal = document.getElementById('closeSystemPreferencesModal');

        // Controls within modals (HVAC)
        const temperatureSlider = document.getElementById('temperature');
        const tempValueSpan = document.getElementById('tempValue');
        const fanSpeedSlider = document.getElementById('fanSpeed');
        const fanValueSpan = document.getElementById('fanValue');

        // Controls within modals (System Preferences)
        const brightnessSlider = document.getElementById('brightnessSlider');
        const brightnessValueSpan = document.getElementById('brightnessValue');
        // Language Buttons INSIDE System Preferences Modal (on Apps Menu Page)
        const langEnButtonModalApps = document.getElementById('langEnButtonModalApps');
        const langDeButtonModalApps = document.getElementById('langDeButtonModalApps');

        // Specific buttons on this Apps Menu page that open modals
        const hvacButtonAppsMenu = document.getElementById('hvacButtonAppsMenu');
        const systemPreferencesButtonAppsMenu = document.getElementById('systemPreferencesButtonAppsMenu');

        const clickSound = document.getElementById('clickSound');

        // Function to play click sound
        function playClickSound() {
            if (clickSound) {
                clickSound.currentTime = 0;
                clickSound.play().catch(e => console.log("Sound play interrupted or failed:", e));
            }
        }

        // --- Language Management ---
        let currentLanguage = 'en'; // Default language, will be updated on DOMContentLoaded

        const translations = {
            'en': {
                title: 'Autonomous Shuttle HMI', // Main dashboard title, not directly used for Apps menu title here
                apps_menu_title: 'Applications', // Title for this page
                back_to_home_menu: 'Back to Home', // Back button text

                // Tile Menu Translations (specific to this page)
                route_button_text: 'Route & Destination',
                shuttle_status_button_text: 'Shuttle Status',
                entertainment_button_text: 'Entertainment',
                emergency_button_text: 'Emergency Assist',
                hvac_button_text: 'HVAC Settings',
                entry_exit_button_text: 'Entry/Exit',
                interior_comfort_button_text: 'Interior Comfort',
                system_preferences_button_text: 'System Preferences',

                // Modal/Info Page translations
                hvac_title: 'HVAC Controls',
                temperature_label: 'Temperature:',
                fan_speed_label: 'Fan Speed:',
                ac_label: 'A/C',
                airflow_label: 'Airflow Direction:',
                face_button: 'Face',
                feet_button: 'Feet',
                defrost_button: 'Defrost',
                sync_climate_button_text: 'Sync Climate',
                system_preferences_title: 'System Preferences',
                brightness_label: 'Brightness:',
                language_label: 'Language:',
                display_setting: 'Display:',
                auto_brightness: 'Auto Brightness (On)',
                audio_setting: 'Audio:',
                voice_prompts: 'Voice Prompts (On)',
                connectivity_setting: 'Connectivity:',
                '5g_active': '5G Active',
            },
            'de': {
                title: 'Autonomes Shuttle HMI',
                apps_menu_title: 'Anwendungen',
                back_to_home_menu: 'Zurück zum Hauptmenü',

                route_button_text: 'Route & Ziel',
                shuttle_status_button_text: 'Shuttle Status',
                entertainment_button_text: 'Unterhaltung',
                emergency_button_text: 'Notfallhilfe',
                hvac_button_text: 'Klima-Einstellungen',
                entry_exit_button_text: 'Ein-/Ausstieg',
                interior_comfort_button_text: 'Innenraumkomfort',
                system_preferences_button_text: 'Systemeinstellungen',

                hvac_title: 'Klima-Steuerung',
                temperature_label: 'Temperatur:',
                fan_speed_label: 'Lüftergeschwindigkeit:',
                ac_label: 'Klimaanlage',
                airflow_label: 'Luftstromrichtung:',
                face_button: 'Gesicht',
                feet_button: 'Füße',
                defrost_button: 'Enteisen',
                sync_climate_button_text: 'Klima synchronisieren',
                system_preferences_title: 'Systemeinstellungen',
                brightness_label: 'Helligkeit:',
                language_label: 'Sprache:',
                display_setting: 'Anzeige:',
                auto_brightness: 'Automatische Helligkeit (Ein)',
                audio_setting: 'Audio:',
                voice_prompts: 'Sprachansagen (Ein)',
                connectivity_setting: 'Konnektivität:',
                '5g_active': '5G Aktiv',
            }
        };

        function updateLanguage(lang) {
            currentLanguage = lang;
            localStorage.setItem('hmiLanguage', lang); // Persist language choice

            document.querySelector('title').textContent = translations[currentLanguage]['apps_menu_title']; // Update title for apps page
            document.querySelector('.info-title').textContent = translations[currentLanguage]['apps_menu_title']; // Update H2 title

            document.querySelectorAll('[data-lang-key]').forEach(element => {
                const key = element.getAttribute('data-lang-key');
                if (translations[currentLanguage][key]) {
                    element.textContent = translations[currentLanguage][key];
                }
            });

            // Update active state for Apps Menu language buttons
            if (langEnButtonAppsMenu) langEnButtonAppsMenu.classList.remove('active');
            if (langDeButtonAppsMenu) langDeButtonAppsMenu.classList.remove('active');
            if (lang === 'en' && langEnButtonAppsMenu) langEnButtonAppsMenu.classList.add('active');
            if (lang === 'de' && langDeButtonAppsMenu) langDeButtonAppsMenu.classList.add('active');


            // Update modal titles when language changes, if modals are visible
            const hvacTitleElement = document.querySelector('#hvacModal .info-title');
            if (hvacTitleElement && translations[currentLanguage]['hvac_title']) {
                hvacTitleElement.textContent = translations[currentLanguage]['hvac_title'];
            }
            const systemPreferencesTitleElement = document.querySelector('#systemPreferencesModal .info-title');
            if (systemPreferencesTitleElement && translations[currentLanguage]['system_preferences_title']) {
                systemPreferencesTitleElement.textContent = translations[currentLanguage]['system_preferences_title'];
            }

            // Re-render modal content if open
            if (systemPreferencesModal && !systemPreferencesModal.classList.contains('hidden')) {
                document.querySelector('#systemPreferencesModal label[data-lang-key="brightness_label"] span').textContent = translations[currentLanguage]['brightness_label'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="language_label"]').textContent = translations[currentLanguage]['language_label'];
                document.querySelector('#systemPreferencesModal p strong[data-lang-key="display_setting"]').textContent = translations[currentLanguage]['display_setting'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="auto_brightness"]').textContent = translations[currentLanguage]['auto_brightness'];
                document.querySelector('#systemPreferencesModal p strong[data-lang-key="audio_setting"]').textContent = translations[currentLanguage]['audio_setting'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="voice_prompts"]').textContent = translations[currentLanguage]['voice_prompts'];
                document.querySelector('#systemPreferencesModal p strong[data-lang-key="connectivity_setting"]').textContent = translations[currentLanguage]['connectivity_setting'];
                document.querySelector('#systemPreferencesModal span[data-lang-key="5g_active"]').textContent = translations[currentLanguage]['5g_active'];
            }
        }

        // --- Generic Modal Functions ---
        function showModal(modalElement) {
            modalElement.classList.remove('hidden');
            setTimeout(() => {
                modalElement.classList.remove('opacity-0');
            }, 10);
        }
        function hideModal(modalElement) {
            modalElement.classList.add('opacity-0');
            setTimeout(() => {
                modalElement.classList.add('hidden');
            }, 300);
        }

        // --- Event Listeners specific to Apps Menu Page ---

        // HVAC Controls from Apps Menu
        if (hvacButtonAppsMenu) {
            hvacButtonAppsMenu.addEventListener('click', () => {
                playClickSound();
                showModal(hvacModal);
            });
        }
        if (closeHvacModal) {
            closeHvacModal.addEventListener('click', () => {
                playClickSound();
                hideModal(hvacModal);
            });
        }
        if (hvacModal) {
            hvacModal.addEventListener('click', (event) => {
                if (event.target === hvacModal) {
                    playClickSound();
                    hideModal(hvacModal);
                }
            });
        }

        // System Preferences from Apps Menu
        if (systemPreferencesButtonAppsMenu) {
            systemPreferencesButtonAppsMenu.addEventListener('click', () => {
                playClickSound();
                showModal(systemPreferencesModal);
            });
        }
        if (closeSystemPreferencesModal) {
            closeSystemPreferencesModal.addEventListener('click', () => {
                playClickSound();
                hideModal(systemPreferencesModal);
            });
        }
        if (systemPreferencesModal) {
            systemPreferencesModal.addEventListener('click', (event) => {
                if (event.target === systemPreferencesModal) {
                    playClickSound();
                    hideModal(systemPreferencesModal);
                }
            });
        }

        // Controls within HVAC modal
        if (temperatureSlider) {
            temperatureSlider.addEventListener('input', (event) => {
                tempValueSpan.textContent = event.target.value;
            });
        }
        if (fanSpeedSlider) {
            fanSpeedSlider.addEventListener('input', (event) => {
                fanValueSpan.textContent = event.target.value;
            });
        }

        // Controls within System Preferences modal
        if (brightnessSlider) {
            brightnessSlider.addEventListener('input', (event) => {
                const brightness = event.target.value;
                brightnessValueSpan.textContent = brightness;
                // Note: appsMenuContainer exists on this page, but its 'filter' property
                // does not behave like hmiContainer's. You'd typically need to apply
                // brightness to the overall body or a root display div.
                // For a consistent system-wide brightness, this needs a native app integration
                // or a different approach for web-only HMI.
                console.log("Brightness changed to " + brightness + "% from Apps Menu.");
            });
        }
        if (langEnButtonModalApps) { // Using the specific modal button ID for Apps Menu's modal
            langEnButtonModalApps.addEventListener('click', () => {
                playClickSound();
                updateLanguage('en'); // Updates language on the current (Apps Menu) page and persists
            });
        }
        if (langDeButtonModalApps) { // Using the specific modal button ID for Apps Menu's modal
            langDeButtonModalApps.addEventListener('click', () => {
                playClickSound();
                updateLanguage('de'); // Updates language on the current (Apps Menu) page and persists
            });
        }


        // Buttons that navigate to other info pages from Apps Menu
        document.querySelectorAll('.hmi-button[data-target-route]').forEach(button => {
            const targetRoute = button.getAttribute('data-target-route');
            button.addEventListener('click', () => {
                playClickSound();
                window.location.href = `/info/${targetRoute}?lang=${currentLanguage}`; // Pass language via URL param
            });
        });

        // --- Header Live Updates (Time, Battery, Temperature) on Apps Menu Page ---
        function updateHeaderInfo() {
            const now = new Date();
            const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            if (currentTimeSpan) currentTimeSpan.textContent = timeString;

            let batteryLevel = parseInt(batteryValueSpan.textContent) || 100;
            if (Math.random() > 0.7) {
                batteryLevel += (Math.random() > 0.5 ? 1 : -1) * Math.floor(Math.random() * 3);
                if (batteryLevel > 100) batteryLevel = 100;
                if (batteryLevel < 0) batteryLevel = 0;
            }
            if (batteryValueSpan) batteryValueSpan.textContent = `${batteryLevel}%`;

            if (batteryIcon) {
                batteryIcon.classList.remove('fa-battery-full', 'fa-battery-three-quarters', 'fa-battery-half', 'fa-battery-quarter', 'fa-battery-empty');
                if (batteryLevel > 75) {
                    batteryIcon.classList.add('fa-battery-full');
                } else if (batteryLevel > 50) {
                    batteryIcon.classList.add('fa-battery-three-quarters');
                } else if (batteryLevel > 25) {
                    batteryIcon.classList.add('fa-battery-half');
                } else if (batteryLevel > 10) {
                    batteryIcon.classList.add('fa-battery-quarter');
                } else {
                    batteryIcon.classList.add('fa-battery-empty');
                    batteryIcon.style.color = 'red';
                }
            }

            let currentTempC = parseFloat(tempDisplaySpan.textContent) || 22;
            if (Math.random() > 0.8) {
                currentTempC += (Math.random() > 0.5 ? 0.5 : -0.5);
                if (currentTempC > 28) currentTempC = 28;
                if (currentTempC < 18) currentTempC = 18;
            }
            if (tempDisplaySpan) tempDisplaySpan.textContent = `${currentTempC.toFixed(0)}°C`;
        }


        document.addEventListener('DOMContentLoaded', () => {
            // Priority: 1. localStorage, 2. URL param, 3. default 'en'
            const savedLang = localStorage.getItem('hmiLanguage');
            const urlLang = new URLSearchParams(window.location.search).get('lang');
            currentLanguage = savedLang || urlLang || 'en'; // Set initial language
            updateLanguage(currentLanguage); // Apply initial language to page elements
            updateHeaderInfo(); // Initial header update
            setInterval(updateHeaderInfo, 5000); // Update header every 5 seconds
        });

    </script>
</body>
</html>
"""

# --- HTML Content for Generic Info Pages (New Window) ---
INFO_PAGE_HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        body {
            font-family: 'Inter', sans-serif;
            overflow: hidden; /* Prevent scrolling */
        }

        /* Consistent background with main HMI */
        .info-page-background {
            background: linear-gradient(135deg, #1c2a3b 0%, #2a3d50 100%);
            position: relative;
            overflow: hidden;
            background-size: 400% 400%;
            animation: gradient-animation 25s ease infinite;
        }

        @keyframes gradient-animation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .info-page-background::before,
        .info-page-background::after {
            content: '';
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            filter: blur(60px);
            opacity: 0.25;
        }

        .info-page-background::before {
            width: 280px;
            height: 280px;
            background: #42a5f5;
            top: 15%;
            left: 8%;
            animation: glow-move-one 22s infinite alternate ease-in-out;
        }

        .info-page-background::after {
            width: 230px;
            height: 230px;
            background: #00bcd4;
            bottom: 12%;
            right: 8%;
            animation: glow-move-two 28s infinite alternate-reverse ease-in-out;
        }

        @keyframes glow-move-one {
            0% { transform: translate(0, 0); }
            50% { transform: translate(55vw, 35vh); }
            100% { transform: translate(0, 0); }
        }

        @keyframes glow-move-two {
            0% { transform: translate(0, 0); }
            50% { transform: translate(-45vw, -25vh); }
            100% { transform: translate(0, 0); }
        }

        /* Back button styling */
        .back-button {
            @apply flex items-center justify-center px-6 py-3 rounded-full shadow-lg transition-all duration-300 ease-in-out transform hover:scale-105;
            background: linear-gradient(145deg, #4a5568, #2d3748);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #e0e7eb;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2),
                        0 6px 12px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }
        .back-button:hover {
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.35),
                        0 10px 20px rgba(0, 0, 0, 0.45),
                        inset 0 1px 0 rgba(255, 255, 255, 0.12);
        }
        .back-button-icon {
            @apply text-3xl mr-3;
            color: #42a5f5;
            text-shadow: 0 0 8px rgba(66, 165, 245, 0.6);
        }
        .back-button-text {
            @apply text-xl font-semibold;
        }

        /* Content area styling */
        .content-area {
            @apply bg-gray-800 p-10 rounded-3xl shadow-2xl w-full mx-auto border border-gray-700;
            background: linear-gradient(160deg, #2a3d50, #1c2a3b);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4),
                        0 20px 40px rgba(0, 0, 0, 0.5),
                        inset 0 2px 0 rgba(255, 255, 255, 0.1);
            min-height: 300px; /* Ensure some height */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .content-area h2 {
            @apply text-3xl font-bold mb-6;
            color: #42a5f5;
        }
        .content-area p {
            @apply text-lg text-gray-200 leading-relaxed mb-2;
        }
    </style>
</head>
<body class="h-screen w-screen flex flex-col items-center justify-center info-page-background text-white p-6">

    <div class="relative z-10 w-full max-w-4xl h-full max-h-[90vh] flex flex-col justify-between">
        <div class="flex justify-between items-center mb-6 text-gray-300">
            <div id="currentTime" class="text-xl font-medium"></div>
            <div class="flex items-center space-x-4">
                <i class="fas fa-wifi text-lg"></i>
                <i id="batteryIcon" class="fas fa-battery-full text-lg"></i>
                <span id="batteryValue" class="text-xl font-medium"></span>
                <span id="tempDisplay" class="text-xl font-medium"></span>
            </div>
        </div>

        <div class="content-area flex-grow">
            <h2 id="pageTitle">{{ title }}</h2>
            <div id="pageContent" class="text-center">
                {{ content | safe }} {# ADDED | safe FILTER HERE #}
            </div>
        </div>

        <div class="mt-8 flex justify-center">
            <a href="/apps_menu?lang={{ lang }}" class="back-button"> {# Link back to apps menu #}
                <i class="back-button-icon fas fa-arrow-left"></i>
                <span class="back-button-text" data-lang-key="back_to_apps_menu">Back to Apps Menu</span>
            </a>
        </div>
    </div>

    <audio id="clickSound" preload="auto">
        <source src="/static/sounds/click.mp3" type="audio/mpeg">
        <source src="/static/sounds/click.wav" type="audio/wav">
        Your browser does not support the audio element.
    </audio>

    <script>
        // Get elements
        const currentTimeSpan = document.getElementById('currentTime');
        const batteryIcon = document.getElementById('batteryIcon');
        const batteryValueSpan = document.getElementById('batteryValue');
        const tempDisplaySpan = document.getElementById('tempDisplay');
        const clickSound = document.getElementById('clickSound');
        const backButtonText = document.querySelector('.back-button-text');
        const pageContentDiv = document.getElementById('pageContent'); // For dynamic content like toggle doors

        // Function to play click sound
        function playClickSound() {
            if (clickSound) {
                clickSound.currentTime = 0; // Reset to start for quick successive clicks
                clickSound.play().catch(e => console.log("Sound play interrupted or failed:", e));
            }
        }

        // --- Language Management (simplified for info page) ---
        // This script will receive the language from the Flask context if needed,
        // but for simplicity, we'll assume it's passed or derived.
        // For now, we'll use a local translation object for the back button.
        const translations = {
            'en': {
                back_to_apps_menu: 'Back to Apps Menu', // NEW translation
                door_status_closed: 'Closed',
                door_status_open: 'Open',
                toggle_doors_button: 'Toggle Doors'
            },
            'de': {
                back_to_apps_menu: 'Zurück zum Apps-Menü', // NEW translation
                door_status_closed: 'Geschlossen',
                door_status_open: 'Offen',
                toggle_doors_button: 'Türen umschalten'
            }
        };

        // Determine current language from URL or a global variable if passed by Flask
        let currentLanguage = 'en'; // Default to English

        // A very basic way to infer language from the URL if Flask passes it as a query param
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('lang')) { // Get language from URL directly
            currentLanguage = urlParams.get('lang');
        }

        function updateInfoPageLanguage() {
            if (backButtonText) {
                // Use the new back_to_apps_menu key
                backButtonText.textContent = translations[currentLanguage]['back_to_apps_menu'];
            }
            // If the page content itself has dynamic elements that need translation, handle them here.
            // For example, the door status text:
            updateDoorStatusText();
        }


        // --- Header Live Updates (Time, Battery, Temperature) ---
        function updateHeaderInfo() {
            // Update Time
            const now = new Date();
            const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            currentTimeSpan.textContent = timeString;

            // Simulate Battery Status (replace with actual API if available on target device)
            let batteryLevel = parseInt(batteryValueSpan.textContent) || 100;
            if (Math.random() > 0.7) {
                batteryLevel += (Math.random() > 0.5 ? 1 : -1) * Math.floor(Math.random() * 3);
                if (batteryLevel > 100) batteryLevel = 100;
                if (batteryLevel < 0) batteryLevel = 0;
            }
            batteryValueSpan.textContent = `${batteryLevel}%`;

            batteryIcon.classList.remove('fa-battery-full', 'fa-battery-three-quarters', 'fa-battery-half', 'fa-battery-quarter', 'fa-battery-empty');
            if (batteryLevel > 75) {
                batteryIcon.classList.add('fa-battery-full');
            } else if (batteryLevel > 50) {
                batteryIcon.classList.add('fa-battery-three-quarters');
            } else if (batteryLevel > 25) {
                batteryIcon.classList.add('fa-battery-half');
            } else if (batteryLevel > 10) {
                batteryIcon.classList.add('fa-battery-quarter');
            } else {
                batteryIcon.classList.add('fa-battery-empty');
                batteryIcon.style.color = 'red';
            }

            // Simulate Temperature (in Celsius)
            let currentTempC = parseFloat(tempDisplaySpan.textContent) || 22;
            if (Math.random() > 0.8) {
                currentTempC += (Math.random() > 0.5 ? 0.5 : -0.5);
                if (currentTempC > 28) currentTempC = 28;
                if (currentTempC < 18) currentTempC = 18;
            }
            tempDisplaySpan.textContent = `${currentTempC.toFixed(0)}°C`;
        }

        // --- Specific Interaction for Entry/Exit Page ---
        let doorsOpen = false; // Initial state for the doors on this page
        function updateDoorStatusText() {
            const doorStatusSpan = document.getElementById('doorStatus');
            if (doorStatusSpan) {
                const baseContent = `Doors are currently:`; // Hardcoded base in JS for now, if not part of Flask content
                if (doorsOpen) {
                    doorStatusSpan.innerHTML = `${baseContent} <span class='text-red-400'>${translations[currentLanguage]['door_status_open']}</span>`;
                } else {
                    doorStatusSpan.innerHTML = `${baseContent} <span class='text-[#00bcd4]'>${translations[currentLanguage]['door_status_closed']}</span>`;
                }
                const toggleButton = document.getElementById('toggleDoorsButton');
                if (toggleButton) {
                    toggleButton.querySelector('span').textContent = translations[currentLanguage]['toggle_doors_button'];
                }
            }
        }

        // Event delegation for toggleDoorsButton inside pageContentDiv (if it exists)
        pageContentDiv.addEventListener('click', (event) => {
            if (event.target.id === 'toggleDoorsButton' || event.target.closest('#toggleDoorsButton')) {
                playClickSound();
                doorsOpen = !doorsOpen;
                updateDoorStatusText();
            }
        });


        // Initial setup on page load
        document.addEventListener('DOMContentLoaded', () => {
            // Priority: 1. localStorage, 2. URL param, 3. default 'en'
            const savedLang = localStorage.getItem('hmiLanguage');
            const urlLang = new URLSearchParams(window.location.search).get('lang');
            currentLanguage = savedLang || urlLang || 'en';
            updateHeaderInfo(); // Initial header update
            updateInfoPageLanguage(); // Apply language to this page
            setInterval(updateHeaderInfo, 5000); // Update header every 5 seconds
        });

    </script>
</body>
</html>
"""

# Define the port for the Flask app
PORT = 5000

# Translations for content that will be rendered by Flask
FLASK_TRANSLATIONS = {
    'en': {
        'route_title': 'Route & Destination',
        'route_content': "<p><strong>Current Route:</strong> Downtown Loop</p><p><strong>Next Stop:</strong> Main Street Station</p><p><strong>Estimated Time:</strong> 5 min</p><div class='mt-4 text-center'><i class='fas fa-route text-6xl text-[#00bcd4]'></i></div>",
        'shuttle_status_title': 'Shuttle Status',
        'shuttle_status_content': "<p><strong>Status:</strong> Autonomous Driving</p><p><strong>Next Service:</strong> 1,200 miles</p><p><strong>Battery:</strong> 85%</p><p><strong>System Diagnostics:</strong> All Green</p><div class='mt-4 text-center'><i class='fas fa-bus text-6xl text-[#00bcd4]'></i></div>",
        'entertainment_title': 'Entertainment', # This is now the "Video" page content
        'entertainment_content': "<p><strong>Now Playing:</strong> 'Future Drive' - Synthwave Collective</p><p><strong>Album:</strong> Neon Horizons</p><p><strong>Artist:</strong> Various</p><div class='flex justify-center items-center mt-4 space-x-4'><i class='fas fa-backward text-4xl text-gray-400 hover:text-white cursor-pointer'></i><i class='fas fa-play-circle text-6xl text-[#00bcd4] hover:text-[#42a5f5] cursor-pointer'></i><i class='fas fa-forward text-4xl text-gray-400 hover:text-white cursor-pointer'></i></div>",
        'emergency_title': 'Emergency Assist',
        'emergency_content': "<p class='text-center text-xl font-bold text-red-400'>Emergency Call Initiated!</p><p class='text-center text-lg mt-2'>Emergency services notified. Stay calm. Assistance en route.</p><div class='mt-4 text-center'><i class='fas fa-life-ring text-6xl text-red-500'></i></div>",
        'entry_exit_title': 'Entry/Exit Control',
        # IMPORTANT: Ensure this content is translated entirely in Flask, or JS for door status needs more logic.
        'entry_exit_content': "<p class='text-center text-xl' id='doorStatus'>Doors are currently: <span class='text-[#00bcd4]'>Closed</span></p><p class='text-center text-lg mt-2'>Doors will open automatically at next designated stop.</p><div class='mt-4 text-center'><button id='toggleDoorsButton' class='hmi-button py-2 px-4 text-sm' style='background: linear-gradient(145deg, #00bcd4, #0097a7);'><i class='fas fa-exchange-alt mr-2'></i> Toggle Doors</button></div>",
        'interior_comfort_title': 'Interior Comfort',
        'interior_comfort_content': "<p class='text-center text-xl'>Lighting: <span class='text-[#00bcd4]'>Ambient</span></p><p class='text-center text-xl'>Temperature: <span class='text-[#00bcd4]'>Optimal (22°C)</span></p><p class='text-center text-xl'>Privacy Mode: <span class='text-[#00bcd4]'>Standard</span></p><div class='mt-4 text-center'><i class='fas fa-couch text-6xl text-[#00bcd4]'></i></div>",
        # New translation key for apps menu page title, used by info page for 'back to apps menu' link
        'apps_menu_title': 'Applications',
    },
    'de': {
        'route_title': 'Route & Ziel',
        'route_content': "<p><strong>Aktuelle Route:</strong> Stadtzentrum-Rundfahrt</p><p><strong>Nächster Halt:</strong> Hauptbahnhof</p><p><strong>Geschätzte Zeit:</strong> 5 Min.</p><div class='mt-4 text-center'><i class='fas fa-route text-6xl text-[#00bcd4]'></i></div>",
        'shuttle_status_title': 'Shuttle Status',
        'shuttle_status_content': "<p><strong>Status:</strong> Autonomes Fahren</p><p><strong>Nächste Wartung:</strong> 1.200 km</p><p><strong>Batterie:</strong> 85%</p><p><strong>Systemdiagnose:</strong> Alles Grün</p><div class='mt-4 text-center'><i class='fas fa-bus text-6xl text-[#00bcd4]'></i></div>",
        'entertainment_title': 'Unterhaltung', # This is now the "Video" page content
        'entertainment_content': "<p><strong>Aktuell:</strong> 'Future Drive' - Synthwave Collective</p><p><strong>Album:</strong> Neon Horizons</p><p><strong>Künstler:</strong> Verschiedene</p><div class='flex justify-center items-center mt-4 space-x-4'><i class='fas fa-backward text-4xl text-gray-400 hover:text-white cursor-pointer'></i><i class='fas fa-play-circle text-6xl text-[#00bcd4] hover:text-[#42a5f5] cursor-pointer'></i><i class='fas fa-forward text-4xl text-gray-400 hover:text-white cursor-pointer'></i></div>",
        'emergency_title': 'Notfallhilfe',
        'emergency_content': "<p class='text-center text-xl font-bold text-red-400'>Notruf eingeleitet!</p><p class='text-center text-lg mt-2'>Rettungsdienste benachrichtigt. Bleiben Sie ruhig. Hilfe unterwegs.</p><div class='mt-4 text-center'><i class='fas fa-life-ring text-6xl text-red-500'></i></div>",
        'hvac_button_text': 'Klima-Einstellungen',
        'hvac_title': 'Klima-Steuerung',
        'temperature_label': 'Temperatur:',
        'fan_speed_label': 'Lüftergeschwindigkeit:',
        'ac_label': 'Klimaanlage',
        'airflow_label': 'Luftstromrichtung:',
        'face_button': 'Gesicht',
        'feet_button': 'Füße',
        'defrost_button': 'Enteisen',
        'sync_climate_button_text': 'Klima synchronisieren',
        'entry_exit_button_text': 'Ein-/Ausstieg',
        'entry_exit_title': 'Ein-/Ausstiegskontrolle',
        'entry_exit_content': "<p class='text-center text-xl' id='doorStatus'>Türen sind derzeit: <span class='text-[#00bcd4]'>Geschlossen</span></p><p class='text-center text-lg mt-2'>Türen öffnen automatisch am nächsten Halt.</p><div class='mt-4 text-center'><button id='toggleDoorsButton' class='hmi-button py-2 px-4 text-sm' style='background: linear-gradient(145deg, #00bcd4, #0097a7);'><i class='fas fa-exchange-alt mr-2'></i> Türen umschalten</button></div>",
        'interior_comfort_button_text': 'Innenraumkomfort',
        'interior_comfort_title': 'Innenraumkomfort',
        'interior_comfort_content': "<p class='text-center text-xl'>Beleuchtung: <span class='text-[#00bcd4]'>Ambiente</span></p><p class='text-center text-xl'>Temperatur: <span class='text-[#00bcd4]'>Optimal (22°C)</span></p><p class='text-center text-xl'>Privatsphäre-Modus: <span class='text-[#00bcd4]'>Standard</span></p><div class='mt-4 text-center'><i class='fas fa-couch text-6xl text-[#00bcd4]'></i></div>",
        'system_preferences_button_text': 'Systemeinstellungen',
        'system_preferences_title': 'Systemeinstellungen',
        'brightness_label': 'Helligkeit:',
        'language_label': 'Sprache:',
        'display_setting': 'Anzeige:',
        'auto_brightness': 'Automatische Helligkeit (Ein)',
        'audio_setting': 'Audio:',
        'voice_prompts': 'Sprachansagen (Ein)',
        'connectivity_setting': 'Konnektivität:',
        '5g_active': '5G Aktiv',
        'lock_status_locked': 'Gesperrt',
        'lock_status_unlocked': 'Entsperrt',
        'volume_status': 'Lautstärke: ',
        'phone_status_calling': 'Anruf läuft...',
        'phone_status_idle': 'Anruf',
        'apps_menu_title': 'Anwendungen',
    }
}


@app.route('/')
def hmi():
    return render_template_string(HMI_HTML_CONTENT)

@app.route('/apps_menu')
def apps_menu():
    # Determine language from query parameter, default to 'en'
    lang = request.args.get('lang', 'en')
    # The Apps Menu HTML will handle its own title and content based on language
    return render_template_string(APPS_MENU_HTML_CONTENT, lang=lang)


# New route for serving dynamic info pages
@app.route('/info/<category>')
def info_page(category):
    # Determine language from query parameter, default to 'en'
    lang = request.args.get('lang', 'en')

    # Get content based on category and language
    title = FLASK_TRANSLATIONS[lang].get(f'{category}_title', 'Information')
    content = FLASK_TRANSLATIONS[lang].get(f'{category}_content', '<p>No information available for this category.</p>')

    # IMPORTANT: Use | safe filter in the template to render raw HTML content
    return render_template_string(INFO_PAGE_HTML_CONTENT, title=title, content=content, lang=lang)


# Route to serve static files (like sounds)
@app.route('/static/sounds/<path:filename>')
def serve_sound(filename):
    return send_from_directory(os.path.join(STATIC_FOLDER, 'sounds'), filename)


def open_browser():
    """Opens the HMI URL in a new browser window after a short delay."""
    time.sleep(1)  # Give the Flask server a moment to start
    webbrowser.open_new(f'http://127.0.0.1:{PORT}/')


if __name__ == '__main__':
    # Create the 'static/sounds' directory if it doesn't exist
    sounds_dir = os.path.join(STATIC_FOLDER, 'sounds')
    os.makedirs(sounds_dir, exist_ok=True)
    print(f"Please place your 'click.mp3' or 'click.wav' file in the directory: {sounds_dir}")
    print("You can download a simple click sound from various free sound effect websites.")

    # Start a new thread to open the browser
    threading.Thread(target=open_browser).start()

    # Run the Flask app
    print(f"Flask HMI running on http://0.0.0.0:{PORT}/")
    print(f"Access from other devices on the same network using your computer's IP address (e.g., 172.21.102.211:{PORT}/)")
    app.run(debug=True, host='0.0.0.0', port=PORT)