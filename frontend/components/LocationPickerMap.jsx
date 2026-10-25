"use client";

import { useEffect, useRef, useState } from "react";
import { MapPin, Navigation, Crosshair, AlertTriangle, CheckCircle, Info } from "lucide-react";

/**
 * Interactive OpenStreetMap component using Leaflet.
 * Features:
 * 1. OpenStreetMap tile layer with required attribution.
 * 2. Visual accuracy radius circle in metres (WGS84 coords.accuracy).
 * 3. Color-coded accuracy indicators (<= 50m green/blue, > 50m amber warning).
 * 4. Interactive map click / marker repositioning for manual pin placement.
 * 5. Robust SVG marker icon (avoids Next.js Leaflet asset-loading 404s).
 * 6. Read-only mode for complaint inspection / review.
 */
export default function LocationPickerMap({
  latitude,
  longitude,
  accuracy,
  readOnly = false,
  onLocationSelect,
  source = null,
  height = "320px",
}) {
  const mapContainerRef = useRef(null);
  const leafletMapRef = useRef(null);
  const markerRef = useRef(null);
  const circleRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Default coordinate (Pune Civic Municipal Center fallback: 18.5204, 73.8567)
  const defaultLat = 18.52043;
  const defaultLon = 73.85674;

  const currentLat = typeof latitude === "number" && !isNaN(latitude) ? latitude : null;
  const currentLon = typeof longitude === "number" && !isNaN(longitude) ? longitude : null;
  const currentAcc = typeof accuracy === "number" && !isNaN(accuracy) && accuracy > 0 ? accuracy : null;

  useEffect(() => {
    let isMounted = true;

    async function initLeaflet() {
      if (typeof window === "undefined" || !mapContainerRef.current) return;

      const L = (await import("leaflet")).default;

      if (!isMounted) return;

      // Clean up previous map instance if re-initializing
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }

      const initialLat = currentLat !== null ? currentLat : defaultLat;
      const initialLon = currentLon !== null ? currentLon : defaultLon;
      const initialZoom = currentLat !== null ? 16 : 13;

      const map = L.map(mapContainerRef.current, {
        center: [initialLat, initialLon],
        zoom: initialZoom,
        zoomControl: true,
      });

      leafletMapRef.current = map;

      // Add OpenStreetMap standard tile layer complying with OSM usage policy
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
      }).addTo(map);

      // Custom high-visibility SVG pin icon to avoid Next.js asset-loader issues
      const createCustomIcon = (isWarning) => {
        const pinColor = isWarning ? "#d97706" : "#2563eb";
        return L.divIcon({
          className: "custom-leaflet-marker",
          html: `
            <div style="position: relative; width: 32px; height: 32px; transform: translate(-50%, -100%);">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="${pinColor}" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3" fill="#ffffff"></circle>
              </svg>
            </div>
          `,
          iconSize: [32, 32],
          iconAnchor: [16, 32],
        });
      };

      // Add pin and accuracy radius if coordinates are present
      if (currentLat !== null && currentLon !== null) {
        const isLowAccuracy = currentAcc !== null && currentAcc > 50;
        const icon = createCustomIcon(isLowAccuracy);

        const marker = L.marker([currentLat, currentLon], {
          icon,
          draggable: !readOnly,
        }).addTo(map);

        markerRef.current = marker;

        if (!readOnly) {
          marker.on("dragend", (e) => {
            const pos = e.target.getLatLng();
            if (onLocationSelect) {
              onLocationSelect({
                latitude: Number(pos.lat.toFixed(6)),
                longitude: Number(pos.lng.toFixed(6)),
                source: "manual_map",
              });
            }
          });
        }

        // Draw accuracy circle
        if (currentAcc !== null) {
          const circleColor = isLowAccuracy ? "#d97706" : "#2563eb";
          const fillColor = isLowAccuracy ? "#fef3c7" : "#bfdbfe";

          const circle = L.circle([currentLat, currentLon], {
            radius: currentAcc,
            color: circleColor,
            fillColor: fillColor,
            fillOpacity: 0.25,
            weight: 1.5,
          }).addTo(map);

          circleRef.current = circle;
        }
      }

      // Allow map click to place or move marker in non-readonly mode
      if (!readOnly) {
        map.on("click", (e) => {
          const { lat, lng } = e.latlng;
          const latFixed = Number(lat.toFixed(6));
          const lonFixed = Number(lng.toFixed(6));

          if (markerRef.current) {
            markerRef.current.setLatLng([lat, lng]);
          } else {
            const icon = createCustomIcon(false);
            const newMarker = L.marker([lat, lng], {
              icon,
              draggable: true,
            }).addTo(map);

            newMarker.on("dragend", (ev) => {
              const pos = ev.target.getLatLng();
              if (onLocationSelect) {
                onLocationSelect({
                  latitude: Number(pos.lat.toFixed(6)),
                  longitude: Number(pos.lng.toFixed(6)),
                  source: "manual_map",
                });
              }
            });

            markerRef.current = newMarker;
          }

          // When manually placed, accuracy circle is removed or minimal
          if (circleRef.current) {
            map.removeLayer(circleRef.current);
            circleRef.current = null;
          }

          if (onLocationSelect) {
            onLocationSelect({
              latitude: latFixed,
              longitude: lonFixed,
              source: "manual_map",
            });
          }
        });
      }

      setMapLoaded(true);
    }

    initLeaflet();

    return () => {
      isMounted = false;
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, [currentLat, currentLon, currentAcc, readOnly]);

  const isLowAccuracy = currentAcc !== null && currentAcc > 50;

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-50 shadow-sm">
      {/* Map Header Status Bar */}
      <div className="px-3 py-2 bg-white/95 backdrop-blur-sm border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <MapPin className={`w-3.5 h-3.5 ${isLowAccuracy ? "text-amber-600" : "text-blue-600"}`} />
          <span className="font-medium text-slate-700">
            {currentLat !== null && currentLon !== null
              ? `${currentLat.toFixed(5)}°, ${currentLon.toFixed(5)}°`
              : "No coordinates pinned yet"}
          </span>
          {source && (
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                source.includes("exif")
                  ? "bg-purple-100 text-purple-700"
                  : source.includes("map")
                  ? "bg-emerald-100 text-emerald-700"
                  : isLowAccuracy
                  ? "bg-amber-100 text-amber-800"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {source.includes("exif")
                ? "Photo EXIF"
                : source.includes("map")
                ? "Map Selected"
                : source.includes("text")
                ? "Manual Address"
                : "Device GPS"}
            </span>
          )}
        </div>

        {currentAcc !== null && (
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-flex items-center gap-1 font-medium ${
                isLowAccuracy ? "text-amber-700" : "text-emerald-700"
              }`}
            >
              {isLowAccuracy ? (
                <AlertTriangle className="w-3 h-3 text-amber-500" />
              ) : (
                <CheckCircle className="w-3 h-3 text-emerald-500" />
              )}
              Accuracy: ±{Math.round(currentAcc)}m
            </span>
          </div>
        )}
      </div>

      {/* Accuracy Warning Banner if > 50m */}
      {isLowAccuracy && !readOnly && (
        <div className="px-3 py-1.5 bg-amber-50 border-b border-amber-200 text-amber-800 text-[11px] flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>
              <strong>Low GPS Accuracy (±{Math.round(currentAcc)}m):</strong> Desktop / Wi-Fi devices approximate location.
              Click the map below to pinpoint the exact road or building.
            </span>
          </div>
        </div>
      )}

      {/* Interactive Leaflet Map Canvas */}
      <div
        ref={mapContainerRef}
        style={{ height, width: "100%", zIndex: 1 }}
        className="w-full relative"
      />

      {/* Map Hint Footer */}
      {!readOnly && (
        <div className="px-3 py-1.5 bg-slate-100/90 border-t border-slate-200 text-slate-500 text-[10px] flex items-center justify-between">
          <span>💡 Click anywhere on the map or drag the pin to adjust incident location</span>
          <span className="text-slate-400">© OpenStreetMap</span>
        </div>
      )}
    </div>
  );
}
