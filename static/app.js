const $ = (id) => document.getElementById(id);

const i18n = {
  ar: {
    brand: 'دلني', tagline: 'أوفر طريق بالباص داخل عمّان', loading: 'جاري تحميل الداتا...',
    locationQuality: 'دقة الموقع الحالي', notDetected: 'لم يتم التحديد بعد', nearestPending: 'أقرب محطة ستظهر بعد تحديد موقعك',
    savingOnly: 'وضع التوفير فقط', mainTitle: 'وين بدك تروح؟', savingBadge: 'أقل تكلفة', from: 'من وين؟', to: 'لوين؟',
    aiButton: 'اسأل دلني', myLocation: 'موقعي الحالي', pickStart: 'حدد البداية', pickEnd: 'حدد الوجهة',
    hint: 'اكتب المكان أو اضغط على الخريطة بعد اختيار البداية أو الوجهة. عندما تحدد النقطتين سيحسب دلني أوفر طريق تلقائيا.',
    routeResult: 'نتيجة الرحلة', savingRoute: 'أوفر مسار مقترح', enableAlert: 'فعّل تنبيه النزول عند 250 متر',
    rateTrip: 'قيّم الرحلة بعد ما تخلص', sendRating: 'إرسال التقييم', generalArea: 'اختيار المنطقة العامة', areaTitle: 'مش فارق الشارع بالزبط؟',
    areaSubtitle: 'اكتب المنطقة اللي أنت فيها والمنطقة اللي بدك توصلها، ودلني يختار أقرب محطات ويوفر عليك.', currentArea: 'منطقة البداية', targetArea: 'منطقة الوجهة', areaSubmit: 'احسب أوفر طريق بالمنطقة',
    dataSummary: 'مصادر البيانات وحدود الدقة', chatTitle: 'شات دلني الذكي', chatHelp: 'احكي أو اكتب رحلتك. دلني يرحب فيك، يفهم طلبك، ثم يحسب أوفر مسار من الداتا.', startVoice: 'تحدث الآن', sendChat: 'إرسال',
    ready: 'جاهز', routing: 'دلني يحسب أوفر طريق...', chooseStart: 'اضغط على الخريطة لاختيار نقطة البداية.', chooseEnd: 'اضغط على الخريطة لاختيار الوجهة.', selected: 'تم التحديد. دلني سيحسب الطريق تلقائيا عند توفر النقطتين.', noGeo: 'المتصفح لا يدعم تحديد الموقع.', locating: 'جاري تحديد الموقع بدقة...', locationSet: 'تم تحديد موقعك الحالي', routeError: 'صار خطأ تقني', noRoute: 'لم يتم العثور على مسار.', alertOn: 'إيقاف تنبيه النزول', alertOff: 'فعّل تنبيه النزول عند 250 متر', alertEnabled: 'تم تفعيل تنبيه النزول.', alertStopped: 'تم إيقاف تنبيه النزول.', feedbackSaved: 'تم حفظ التقييم، شكرا إلك.', unsupportedVoice: 'المتصفح لا يدعم التعرف على الصوت. جرّب Chrome.', listening: 'اسمعك...', voiceDone: 'تم التقاط الكلام. راجعه ثم اضغط إرسال.',
    walk: 'مشي', bus: 'باص', line: 'خط', fare: 'التكلفة', time: 'الوقت', arrival: 'الوصول', walking: 'المشي', walkDistance: 'مسافة المشي', transfers: 'التبديلات', quality: 'التقييم', nearestStart: 'أقرب محطة للبداية', nearestEnd: 'أقرب محطة للوجهة', routeSteps: 'خطوات الرحلة', passedStops: 'المحطات على الخط', rating: 'تقييم', minutes: 'دقيقة', meters: 'متر', jd: 'دينار', exactWalk: 'مسار المشي على الخريطة من OpenStreetMap عند توفر الإنترنت', car: 'سيارة', accessToStation: 'الوصول للمحطة', carAccess: 'إذا معك سيارة', walkAccess: 'إذا بدك تمشي', fullCarAccess: 'تقدير السيارة للمحطة',
  },
  en: {
    brand: 'Dellni', tagline: 'Lowest-cost bus routing in Amman', loading: 'Loading data...',
    locationQuality: 'Current location accuracy', notDetected: 'Not detected yet', nearestPending: 'Nearest stop appears after location is set',
    savingOnly: 'Savings mode only', mainTitle: 'Where are you going?', savingBadge: 'Lowest cost', from: 'Start', to: 'Destination',
    aiButton: 'Ask Dellni', myLocation: 'My location', pickStart: 'Pick start', pickEnd: 'Pick destination',
    hint: 'Type a place or press the map after choosing start or destination. Dellni calculates automatically when both points are set.',
    routeResult: 'Trip result', savingRoute: 'Lowest-cost route', enableAlert: 'Enable 250 m exit alert',
    rateTrip: 'Rate the trip when finished', sendRating: 'Send rating', generalArea: 'General area mode', areaTitle: 'No exact street needed?',
    areaSubtitle: 'Type your start area and target area; Dellni chooses nearby stops to save cost.', currentArea: 'Start area', targetArea: 'Target area', areaSubmit: 'Calculate by area',
    dataSummary: 'Data sources and accuracy limits', chatTitle: 'Dellni AI chat', chatHelp: 'Write or speak your trip. Dellni greets you, understands the request, then calculates from verified data.', startVoice: 'Speak now', sendChat: 'Send',
    ready: 'Ready', routing: 'Dellni is calculating...', chooseStart: 'Press the map to choose the start point.', chooseEnd: 'Press the map to choose the destination.', selected: 'Point selected. Dellni will calculate automatically when both points are available.', noGeo: 'Your browser does not support geolocation.', locating: 'Getting precise location...', locationSet: 'Current location set', routeError: 'Technical error', noRoute: 'No route found.', alertOn: 'Stop exit alert', alertOff: 'Enable 250 m exit alert', alertEnabled: 'Exit alert enabled.', alertStopped: 'Exit alert stopped.', feedbackSaved: 'Rating saved. Thank you.', unsupportedVoice: 'Speech recognition is not supported. Try Chrome.', listening: 'Listening...', voiceDone: 'Speech captured. Review it, then press Send.',
    walk: 'Walk', bus: 'Bus', line: 'Line', fare: 'Fare', time: 'Time', arrival: 'Arrival', walking: 'Walking', walkDistance: 'Walking distance', transfers: 'Transfers', quality: 'Rating', nearestStart: 'Nearest start stop', nearestEnd: 'Nearest destination stop', routeSteps: 'Trip steps', passedStops: 'Stops on this line', rating: 'Rating', minutes: 'min', meters: 'm', jd: 'JD', exactWalk: 'Walking route is drawn from OpenStreetMap when online', car: 'Car', accessToStation: 'Access to station', carAccess: 'If you have a car', walkAccess: 'If you walk', fullCarAccess: 'Car to station estimate',
  }
};

let lang = 'ar';
let map, routeLayer, markerLayer, pickerLayer, accuracyLayer;
let currentRoute = null;
let activePicker = null;
let originCoords = null;
let destinationCoords = null;
let originMarker = null;
let destinationMarker = null;
let watchId = null;
let routeDebounce = null;
let lastRouteKey = '';
let cachedLocations = [];
let cachedRoutes = [];
let osrmCache = new Map();
let chatStarted = false;
let chatHistory = [];

function setMobileViewportHeight() {
  const visualHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
  const height = Math.max(520, Math.round(visualHeight || window.innerHeight || 720));
  document.documentElement.style.setProperty('--app-height', `${height}px`);
}
function safeInvalidateMap() {
  if (!map) return;
  window.requestAnimationFrame(() => {
    try { map.invalidateSize({animate:false}); } catch (_) {}
  });
}
function isCompactViewport() {
  return window.matchMedia('(max-width: 900px)').matches;
}
function fitMapToPoints(points, options={}) {
  if (!map || !points || !points.length) return;
  const bounds = L.latLngBounds(points);
  const compact = isCompactViewport();
  const paddingTopLeft = compact ? [34, 96] : [90, 90];
  const paddingBottomRight = compact ? [34, Math.min(380, Math.round(window.innerHeight * 0.52))] : [90, 90];
  try {
    if (points.length === 1) map.setView(points[0], options.zoom || 16);
    else map.fitBounds(bounds, {paddingTopLeft, paddingBottomRight, maxZoom: options.maxZoom || 15});
  } catch (_) {}
  safeInvalidateMap();
}

function t(key) { return i18n[lang][key] || i18n.ar[key] || key; }
function esc(v) { return String(v ?? '').replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function fmtMoney(v) { return `${Number(v || 0).toFixed(2)} ${t('jd')}`; }
function fmtMeters(v) { return `${Math.round(Number(v || 0))} ${t('meters')}`; }
function fmtMinutes(v) { return `${Number(v || 0).toFixed(1)} ${t('minutes')}`; }

function applyLanguage() {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.body.classList.toggle('lang-en', lang === 'en');
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  $('langToggle').textContent = lang === 'ar' ? 'English' : 'العربية';
  $('origin').placeholder = lang === 'ar' ? 'مثال: صويلح أو موقعي الحالي' : 'Example: Sweileh or my location';
  $('destination').placeholder = lang === 'ar' ? 'مثال: العبدلي أو الزرقاء' : 'Example: Abdali or Zarqa';
  $('areaOrigin').placeholder = lang === 'ar' ? 'مثال: خلدا' : 'Example: Khalda';
  $('areaDestination').placeholder = lang === 'ar' ? 'مثال: العبدلي' : 'Example: Abdali';
  if ($('chatInput')) $('chatInput').placeholder = lang === 'ar' ? 'احكي مثلاً: من صويلح إلى 42 عمان الساعة ٨' : 'Example: from Sweileh to 42 Amman at 8';
  setStatus(currentRoute ? t('ready') : t('ready'));
  if (currentRoute) renderAssistantResult(currentRoute, false);
}

function nowForDateTimeInput() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}
async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  return await response.json();
}
async function postJson(url, payload) {
  const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  return await response.json();
}
function setStatus(text) { $('systemStatus').textContent = text; }
function setBusy(isBusy) {
  document.querySelectorAll('button').forEach((btn) => { if (!['langToggle'].includes(btn.id)) btn.disabled = isBusy && btn.classList.contains('primary-submit'); });
  setStatus(isBusy ? t('routing') : t('ready'));
}

function initMap() {
  setMobileViewportHeight();
  map = L.map('map', {scrollWheelZoom: true, zoomControl: false, tap: true}).setView([31.9632, 35.9304], 12);
  L.control.zoom({position: 'bottomleft'}).addTo(map);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}).addTo(map);
  routeLayer = L.layerGroup().addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  pickerLayer = L.layerGroup().addTo(map);
  accuracyLayer = L.layerGroup().addTo(map);
  map.on('click', (e) => handleMapClick(e.latlng));
  map.whenReady(() => {
    safeInvalidateMap();
    setTimeout(safeInvalidateMap, 250);
    setTimeout(safeInvalidateMap, 900);
  });
}

function setPicker(which) {
  activePicker = which;
  $('pickerHint').textContent = which === 'origin' ? t('chooseStart') : t('chooseEnd'); lastRouteKey = '';
  document.body.classList.add('picking-map');
}
function handleMapClick(latlng) {
  if (!activePicker) return;
  const coords = {lat: latlng.lat, lon: latlng.lng, name: activePicker === 'origin' ? (lang === 'ar' ? 'نقطة بداية محددة' : 'Pinned start') : (lang === 'ar' ? 'وجهة محددة' : 'Pinned destination')};
  if (activePicker === 'origin') setOriginCoords(coords, true);
  else setDestinationCoords(coords, true);
  activePicker = null;
  document.body.classList.remove('picking-map');
  $('pickerHint').textContent = t('selected');
  maybeAutoRoute();
}

function clearOriginCoordinateSelection() {
  originCoords = null;
  if (originMarker) { pickerLayer.removeLayer(originMarker); originMarker = null; }
  lastRouteKey = '';
}
function clearDestinationCoordinateSelection() {
  destinationCoords = null;
  if (destinationMarker) { pickerLayer.removeLayer(destinationMarker); destinationMarker = null; }
  lastRouteKey = '';
}

function markerIcon(kind) {
  const color = kind === 'origin' ? '#e8b66c' : '#bd754d';
  const label = kind === 'origin' ? '●' : '◆';
  return L.divIcon({className:'user-marker', html:`<div style="width:34px;height:34px;border-radius:14px;background:${color};display:grid;place-items:center;color:white;font-weight:900;border:3px solid white;box-shadow:0 10px 24px rgba(0,0,0,.18)">${label}</div>`, iconSize:[34,34], iconAnchor:[17,17]});
}
function setOriginCoords(coords, updateInput) {
  originCoords = coords;
  lastRouteKey = '';
  if (updateInput) $('origin').value = coords.name || (lang === 'ar' ? 'موقع محدد من الخريطة' : 'Pinned start');
  drawPickers();
}
function setDestinationCoords(coords, updateInput) {
  destinationCoords = coords;
  lastRouteKey = '';
  if (updateInput) $('destination').value = coords.name || (lang === 'ar' ? 'وجهة محددة من الخريطة' : 'Pinned destination');
  drawPickers();
}
function drawPickers() {
  pickerLayer.clearLayers();
  const bounds = [];
  if (originCoords) {
    originMarker = L.marker([originCoords.lat, originCoords.lon], {icon: markerIcon('origin'), draggable:true}).addTo(pickerLayer).bindPopup(t('from'));
    originMarker.on('dragend', () => {
      const p = originMarker.getLatLng();
      setOriginCoords({lat:p.lat, lon:p.lng, name: lang === 'ar' ? 'نقطة بداية معدلة' : 'Adjusted start'}, false);
      maybeAutoRoute();
    });
    bounds.push([originCoords.lat, originCoords.lon]);
  }
  if (destinationCoords) {
    destinationMarker = L.marker([destinationCoords.lat, destinationCoords.lon], {icon: markerIcon('destination'), draggable:true}).addTo(pickerLayer).bindPopup(t('to'));
    destinationMarker.on('dragend', () => {
      const p = destinationMarker.getLatLng();
      setDestinationCoords({lat:p.lat, lon:p.lng, name: lang === 'ar' ? 'وجهة معدلة' : 'Adjusted destination'}, false);
      maybeAutoRoute();
    });
    bounds.push([destinationCoords.lat, destinationCoords.lon]);
  }
  if (bounds.length) fitMapToPoints(bounds, {zoom:16, maxZoom:15});
}

function usePreciseLocation() {
  if (!navigator.geolocation) {
    $('accuracyText').textContent = t('noGeo');
    return;
  }
  $('accuracyText').textContent = t('locating');
  $('nearestStopText').textContent = '';
  let best = null;
  let completed = false;
  const start = Date.now();
  const finish = async () => {
    if (completed || !best) return;
    completed = true;
    navigator.geolocation.clearWatch(tempWatch);
    const coords = {lat: best.coords.latitude, lon: best.coords.longitude, accuracy: best.coords.accuracy, name: lang === 'ar' ? 'موقعي الحالي' : 'My current location'};
    setOriginCoords(coords, true);
    $('origin').value = lang === 'ar' ? 'موقعي الحالي' : 'My current location';
    $('accuracyText').textContent = `${t('locationSet')} · ±${Math.round(coords.accuracy)} ${t('meters')}`;
    drawAccuracy(coords);
    await updateNearestStop(coords);
    maybeAutoRoute();
  };
  const tempWatch = navigator.geolocation.watchPosition((pos) => {
    if (!best || pos.coords.accuracy < best.coords.accuracy) {
      best = pos;
      $('accuracyText').textContent = `${t('locating')} ±${Math.round(pos.coords.accuracy)} ${t('meters')}`;
      drawAccuracy({lat:pos.coords.latitude, lon:pos.coords.longitude, accuracy:pos.coords.accuracy});
    }
    if (pos.coords.accuracy <= 15 || Date.now() - start > 18000) finish();
  }, (err) => {
    $('accuracyText').textContent = err.message;
  }, {enableHighAccuracy:true, maximumAge:0, timeout:15000});
  setTimeout(finish, 19000);
}
function drawAccuracy(coords) {
  accuracyLayer.clearLayers();
  if (!coords || !coords.lat || !coords.lon) return;
  L.circle([coords.lat, coords.lon], {radius: coords.accuracy || 30, color:'#e8b66c', fillColor:'#e8b66c', fillOpacity:.10, weight:2}).addTo(accuracyLayer);
}
async function updateNearestStop(coords) {
  try {
    const res = await postJson('/api/nearest-stop', {lat:coords.lat, lon:coords.lon});
    if (res.status === 'ok') {
      const n = res.nearest;
      $('nearestStopText').textContent = `${n.name} · ${n.walk_minutes} ${t('minutes')} ${t('walk')}`;
    }
  } catch (_) {}
}

function payloadFromInputs() {
  const payload = {departure_time:$('departureTime').value, language:lang, priority:'lowest_cost'};
  const originText = $('origin').value.trim();
  const destinationText = $('destination').value.trim();
  if (originCoords) payload.origin_coords = originCoords; else payload.origin = originText;
  if (destinationCoords) payload.destination_coords = destinationCoords; else payload.destination = destinationText;
  return payload;
}
function hasRouteInput() {
  return (originCoords || $('origin').value.trim()) && (destinationCoords || $('destination').value.trim());
}
function maybeAutoRoute() {
  clearTimeout(routeDebounce);
  routeDebounce = setTimeout(() => {
    if (!hasRouteInput()) return;
    const payload = payloadFromInputs();
    const key = JSON.stringify(payload);
    if (key === lastRouteKey) return;
    lastRouteKey = key;
    submitRoute(payload, '/api/route');
  }, 450);
}
async function submitRoute(payload, endpoint='/api/route') {
  setBusy(true);
  try {
    const data = await postJson(endpoint, payload);
    renderAssistantResult(data, true);
  } catch (error) {
    showResultError(`${t('routeError')}: ${error.message}`);
  } finally {
    setBusy(false);
  }
}
function showResultError(text) {
  $('resultPanel').classList.remove('hidden');
  $('assistantCard').textContent = text;
  $('summaryCards').innerHTML = '';
  $('nearestBox').innerHTML = '';
  if ($('accessBox')) $('accessBox').innerHTML = '';
  $('stepsBox').innerHTML = '';
  $('tripFeedback').classList.add('hidden');
}

function renderAssistantResult(data, scrollToResult=true) {
  currentRoute = data;
  $('resultPanel').classList.remove('hidden');
  if (data.status !== 'ok') {
    $('assistantCard').textContent = data.assistant_text || data.message || t('noRoute');
    renderNearest(data.nearest);
    if ($('accessBox')) $('accessBox').innerHTML = '';
    $('summaryCards').innerHTML = '';
    $('stepsBox').innerHTML = '';
    $('tripFeedback').classList.add('hidden');
    safeInvalidateMap();
    if (scrollToResult && !isCompactViewport()) $('resultPanel').scrollIntoView({behavior:'smooth', block:'start'});
    return;
  }
  $('assistantCard').textContent = data.assistant_text || '';
  renderSummary(data);
  renderAccess(data);
  renderNearest(data.nearest);
  renderSteps(data);
  renderMap(data);
  $('tripFeedback').classList.remove('hidden');
  $('alertBtn').disabled = !data.proximity_target;
  $('alertBtn').textContent = t('alertOff');
  safeInvalidateMap();
  if (scrollToResult && !isCompactViewport()) $('resultPanel').scrollIntoView({behavior:'smooth', block:'start'});
}
function renderSummary(data) {
  const cards = [
    [t('fare'), fmtMoney(data.fare_jd), '💳'],
    [t('time'), fmtMinutes(data.total_duration_minutes), '⏱️'],
    [t('arrival'), data.arrival_time ? data.arrival_time.slice(-8, -3) : '--', '🏁'],
    [t('walking'), fmtMinutes(data.walking_minutes || 0), '🚶'],
    [t('walkDistance'), fmtMeters(data.walking_distance_m || 0), '📏'],
    [t('quality'), data.route_quality?.average ? `${data.route_quality.average}/5` : '--', '⭐'],
  ];
  $('summaryCards').innerHTML = cards.map(([label,value,icon]) => `<article class="summary-card"><span>${icon} ${esc(label)}</span><strong>${esc(value)}</strong></article>`).join('');
}

function renderAccess(data) {
  const box = $('accessBox');
  if (!box) return;
  const access = data.access_to_first_stop;
  if (!access) { box.innerHTML = ''; return; }
  const carAlt = access.car_to_station_then_bus || data.car_access_to_station_estimate || {};
  const firstBus = (data.legs || []).find((leg) => leg.mode === 'bus') || {};
  box.innerHTML = `
    <article class="access-card primary-access">
      <div class="access-icon">🚶</div>
      <div>
        <b>${t('walkAccess')}</b>
        <strong>${esc(access.name)}</strong>
        <p>${fmtMeters(access.distance_m)} · ${fmtMinutes(access.walk_minutes)} ${t('walk')}</p>
      </div>
    </article>
    <article class="access-card car-access">
      <div class="access-icon">🚗</div>
      <div>
        <b>${t('carAccess')}</b>
        <strong>${fmtMinutes(access.car_minutes)} ${t('car')}</strong>
        <p>${fmtMeters(access.car_distance_m || access.distance_m)} ${lang === 'ar' ? 'إلى نفس المحطة' : 'to the same station'}</p>
        ${carAlt.estimated_total_minutes_if_car_to_station ? `<small>${t('fullCarAccess')}: ${fmtMinutes(carAlt.estimated_total_minutes_if_car_to_station)} · ${fmtMoney(carAlt.public_transport_fare_jd || data.fare_jd)}</small>` : ''}
      </div>
    </article>
    <article class="access-card bus-after-access">
      <div class="access-icon">🚌</div>
      <div>
        <b>${lang === 'ar' ? 'بعد الوصول للمحطة' : 'After reaching station'}</b>
        <strong>${firstBus.route_no ? `${t('line')} ${esc(firstBus.route_no)}` : esc(firstBus.route_name || '--')}</strong>
        <p>${esc(firstBus.from_name || access.name)} ← ${esc(firstBus.to_name || '')}</p>
      </div>
    </article>`;
}

function renderNearest(nearest) {
  if (!nearest) { $('nearestBox').innerHTML = ''; return; }
  const rows = [
    [t('nearestStart'), nearest.origin],
    [t('nearestEnd'), nearest.destination],
  ];
  $('nearestBox').innerHTML = rows.filter(([,n]) => n).map(([title,n]) => `
    <article class="nearest-card">
      <b>${esc(title)}</b>
      <strong>${esc(n.name)}</strong>
      <small>${fmtMinutes(n.walk_minutes)} ${t('walk')} · ${n.car_minutes ? `${fmtMinutes(n.car_minutes)} ${t('car')}` : ''} · ${fmtMeters(n.distance_m)} · ${t('rating')} ${esc(n.station_rating || '--')}/5</small>
      <small>${esc(lang === 'ar' ? n.label_ar : n.label_en)}</small>
    </article>`).join('');
}
function legTitle(leg, index) {
  if (leg.mode === 'bus') return `${index}. ${t('bus')} · ${t('line')} ${leg.route_no || leg.route_id || ''}`;
  if (leg.is_access_leg) return `${index}. ${t('accessToStation')}`;
  return `${index}. ${t('walk')}`;
}
function renderSteps(data) {
  const legs = data.legs || [];
  const html = `<h3>${t('routeSteps')}</h3><ol>${legs.map((leg, i) => {
    const meta = leg.mode === 'bus'
      ? `${esc(leg.from_name)} ← ${esc(leg.to_name)} · ${fmtMinutes(leg.duration_minutes)} · ${fmtMoney(leg.fare_jd)}`
      : `${esc(leg.from_name)} ← ${esc(leg.to_name)} · ${fmtMinutes(leg.duration_minutes)} ${t('walk')}${leg.car_minutes ? ` · ${fmtMinutes(leg.car_minutes)} ${t('car')}` : ''} · ${fmtMeters(leg.distance_m || 0)}`;
    const stops = leg.mode === 'bus' && leg.intermediate_stops && leg.intermediate_stops.length
      ? `<details><summary>${t('passedStops')}</summary><ol class="stop-list">${leg.intermediate_stops.map((s) => `<li>${esc(s.name)} · ⭐ ${esc(s.station_rating || '--')}</li>`).join('')}</ol></details>`
      : `<small>${esc(leg.is_access_leg ? (lang === 'ar' ? (leg.access_label_ar || t('exactWalk')) : (leg.access_label_en || t('exactWalk'))) : t('exactWalk'))}</small>`;
    return `<li class="step-item"><div class="step-head"><div class="step-title"><span class="step-number">${i+1}</span><strong>${esc(legTitle(leg, i+1))}</strong></div></div><div class="step-meta">${meta}</div>${stops}</li>`;
  }).join('')}</ol>`;
  $('stepsBox').innerHTML = html;
}

function legColor(leg) {
  if (leg.mode === 'bus') return '#2a0b45';
  return '#bd754d';
}
async function renderMap(data) {
  routeLayer.clearLayers();
  markerLayer.clearLayers();
  const points = [];
  const origin = data.map?.origin;
  const destination = data.map?.destination;
  if (origin) { points.push([origin.lat, origin.lon]); L.marker([origin.lat, origin.lon], {icon: markerIcon('origin')}).addTo(markerLayer).bindPopup(esc(origin.name)); }
  if (destination) { points.push([destination.lat, destination.lon]); L.marker([destination.lat, destination.lon], {icon: markerIcon('destination')}).addTo(markerLayer).bindPopup(esc(destination.name)); }
  for (const leg of (data.legs || [])) {
    let geometry = (leg.geometry || []).filter((p) => Array.isArray(p) && p.length === 2);
    if (leg.mode === 'walk' && leg.from_coord && leg.to_coord) {
      const routed = await getWalkingGeometry(leg.from_coord, leg.to_coord);
      if (routed && routed.length >= 2) geometry = routed;
    }
    if (leg.mode === 'bus' && geometry.length >= 2) {
      const roadLine = await getRoadGeometry(geometry, 'driving');
      if (roadLine && roadLine.length >= 2) geometry = roadLine;
    }
    if (geometry.length >= 2) {
      L.polyline(geometry, {color: legColor(leg), weight: leg.mode === 'bus' ? 7 : 5, opacity: .92, dashArray: leg.mode === 'walk' ? '8 10' : null}).addTo(routeLayer).bindPopup(esc(`${leg.mode === 'bus' ? t('bus') : t('walk')}: ${leg.from_name} → ${leg.to_name}`));
      points.push(...geometry);
    }
  }
  for (const marker of (data.map?.stop_markers || [])) {
    if (marker.lat && marker.lon) {
      L.circleMarker([marker.lat, marker.lon], {radius:7, weight:2, fillOpacity:.9, color:'#fff', fillColor:'#e8b66c'}).addTo(markerLayer).bindPopup(esc(marker.name || 'محطة'));
      points.push([marker.lat, marker.lon]);
    }
  }
  if (points.length) fitMapToPoints(points, {maxZoom:15});
}

async function getRoadGeometry(points, profile='driving') {
  const clean = (points || []).filter((p) => Array.isArray(p) && p.length === 2 && Number.isFinite(Number(p[0])) && Number.isFinite(Number(p[1])));
  if (clean.length < 2) return clean;
  const simplified = [];
  for (const p of clean) {
    const last = simplified[simplified.length - 1];
    if (!last || Math.abs(last[0]-p[0]) > 0.00001 || Math.abs(last[1]-p[1]) > 0.00001) simplified.push([Number(p[0]), Number(p[1])]);
  }
  const key = `${profile}:${simplified.map((p) => p.join(',')).join(';')}`;
  if (osrmCache.has(key)) return osrmCache.get(key);
  const chunks = [];
  for (let i = 0; i < simplified.length - 1; i++) {
    const a = simplified[i];
    const b = simplified[i + 1];
    const url = `https://router.project-osrm.org/route/v1/${profile}/${a[1]},${a[0]};${b[1]},${b[0]}?overview=full&geometries=geojson&steps=false`;
    try {
      const response = await fetch(url, {cache:'force-cache'});
      if (!response.ok) throw new Error('Road route unavailable');
      const data = await response.json();
      const coords = data.routes?.[0]?.geometry?.coordinates;
      if (!coords || !coords.length) throw new Error('No road geometry');
      const line = coords.map(([lon, lat]) => [lat, lon]);
      if (chunks.length && line.length) line.shift();
      chunks.push(...line);
    } catch (_) {
      if (chunks.length) chunks.push(b); else chunks.push(a, b);
    }
  }
  const out = chunks.length >= 2 ? chunks : simplified;
  osrmCache.set(key, out);
  return out;
}

async function getWalkingGeometry(fromCoord, toCoord) {
  const key = `${fromCoord.join(',')};${toCoord.join(',')}`;
  if (osrmCache.has(key)) return osrmCache.get(key);
  const [lat1, lon1] = fromCoord;
  const [lat2, lon2] = toCoord;
  const url = `https://router.project-osrm.org/route/v1/foot/${lon1},${lat1};${lon2},${lat2}?overview=full&geometries=geojson&steps=false`;
  try {
    const response = await fetch(url, {cache:'force-cache'});
    if (!response.ok) throw new Error('OSM route unavailable');
    const data = await response.json();
    const coords = data.routes?.[0]?.geometry?.coordinates;
    if (!coords || !coords.length) throw new Error('No geometry');
    const line = coords.map(([lon, lat]) => [lat, lon]);
    osrmCache.set(key, line);
    return line;
  } catch (_) {
    const fallback = [fromCoord, toCoord];
    osrmCache.set(key, fallback);
    return fallback;
  }
}

function haversineMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000, toRad = (d) => d * Math.PI / 180;
  const p1 = toRad(lat1), p2 = toRad(lat2), dp = toRad(lat2-lat1), dl = toRad(lon2-lon1);
  const a = Math.sin(dp/2)**2 + Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}
function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = 880;
    gain.gain.value = .06;
    osc.connect(gain); gain.connect(ctx.destination); osc.start();
    setTimeout(() => { osc.stop(); ctx.close(); }, 350);
  } catch (_) {}
}
function toggleExitAlert() {
  if (!currentRoute || !currentRoute.proximity_target) return;
  if (!navigator.geolocation) { alert(t('noGeo')); return; }
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId); watchId = null;
    $('alertBtn').textContent = t('alertOff');
    $('pickerHint').textContent = t('alertStopped');
    return;
  }
  const target = currentRoute.proximity_target;
  $('alertBtn').textContent = t('alertOn');
  $('pickerHint').textContent = t('alertEnabled');
  if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();
  watchId = navigator.geolocation.watchPosition((pos) => {
    const d = haversineMeters(pos.coords.latitude, pos.coords.longitude, target.lat, target.lon);
    $('alertBtn').textContent = `${t('alertOn')} · ${Math.round(d)} ${t('meters')}`;
    if (d <= (target.radius_m || 250)) {
      if (navigator.vibrate) navigator.vibrate([300, 120, 300, 120, 300]);
      beep();
      const message = lang === 'ar' ? target.message_ar : target.message_en;
      if ('Notification' in window && Notification.permission === 'granted') new Notification('Dellni', {body: message});
      alert(message);
      navigator.geolocation.clearWatch(watchId); watchId = null;
      $('alertBtn').textContent = t('alertOff');
      $('tripFeedback').classList.remove('hidden');
      $('tripFeedback').scrollIntoView({behavior:'smooth', block:'center'});
    }
  }, (err) => { $('pickerHint').textContent = err.message; }, {enableHighAccuracy:true, maximumAge:0, timeout:15000});
}


function setupVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;
  const recognition = new SpeechRecognition();
  recognition.lang = lang === 'ar' ? 'ar-JO' : 'en-US';
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 3;
  recognition.onstart = () => { $('voiceStatus').textContent = t('listening'); $('startVoiceBtn').classList.add('recording'); };
  recognition.onend = () => { $('startVoiceBtn').classList.remove('recording'); };
  recognition.onerror = (event) => { $('voiceStatus').textContent = event.error; $('startVoiceBtn').classList.remove('recording'); };
  recognition.onresult = (event) => {
    let finalText = '';
    let interimText = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const txt = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += txt;
      else interimText += txt;
    }
    const current = (finalText || interimText || '').trim();
    if (current) {
      $('chatInput').value = current;
      $('voiceStatus').textContent = finalText ? t('voiceDone') : current;
    }
  };
  $('startVoiceBtn').addEventListener('click', () => {
    recognition.lang = lang === 'ar' ? 'ar-JO' : 'en-US';
    recognition.start();
  });
}
function addChatMessage(role, text) {
  const wrap = document.createElement('div');
  wrap.className = `chat-bubble ${role}`;
  if (role.includes('thinking')) {
    wrap.innerHTML = '<span class="typing-dots" aria-label="..."><i></i><i></i><i></i></span>';
  } else {
    wrap.textContent = text;
  }
  $('chatMessages').appendChild(wrap);
  $('chatMessages').scrollTop = $('chatMessages').scrollHeight;
}
function openVoice() {
  $('aiDialog').showModal();
  if (!chatStarted) {
    chatStarted = true;
    const greeting = lang === 'ar'
      ? 'أهلًا! أنا دلني. احكيلي من وين لوين والساعة كم. إذا المكان مش موجود بالقائمة، بدوّره على الخريطة وبحسبلك أوفر مسار بالباص وأقرب محطة.'
      : 'Hi, I’m Dellni. Tell me your start, destination and time, and I’ll calculate the lowest-cost bus route.';
    addChatMessage('assistant', greeting);
  }
  setTimeout(() => $('chatInput').focus(), 100);
}
async function sendChatMessage() {
  const message = $('chatInput').value.trim();
  if (!message) return;
  $('chatInput').value = '';
  $('voiceStatus').textContent = '';
  addChatMessage('user', message);
  try {
    addChatMessage('assistant thinking', '...');
    const data = await postJson('/api/ai-chat', {message, language: lang, departure_time: $('departureTime').value, current_route: currentRoute});
    const thinking = $('chatMessages').querySelector('.thinking:last-child');
    if (thinking) thinking.remove();
    addChatMessage('assistant', data.assistant_text || 'تم.');
    if (data.route) renderAssistantResult(data.route, false);
  } catch (error) {
    const thinking = $('chatMessages').querySelector('.thinking:last-child');
    if (thinking) thinking.remove();
    addChatMessage('assistant', `${t('routeError')}: ${error.message}`);
  }
}


function populateLocations(locations) {
  cachedLocations = locations;
  const list = $('locationsList');
  list.innerHTML = '';
  locations.forEach((loc) => {
    const opt = document.createElement('option');
    opt.value = loc.name;
    opt.label = loc.landmark || loc.type;
    list.appendChild(opt);
  });
}
function renderDataQuality(data) {
  const metadata = data.metadata || {};
  const counts = data.counts || {};
  $('datasetWarning').textContent = metadata.important_note || '';
  const cards = [
    [lang === 'ar' ? 'المحطات' : 'Stops', counts.stops],
    [lang === 'ar' ? 'اتجاهات الخطوط' : 'Route directions', counts.route_directions],
    [lang === 'ar' ? 'الرحلات' : 'Trips', counts.trips],
    [lang === 'ar' ? 'وصلات المشي' : 'Walking links', counts.footpaths],
    [lang === 'ar' ? 'مصدر الملف' : 'Data file', metadata.source_file || 'JSON'],
    [lang === 'ar' ? 'حدود AI' : 'AI boundary', lang === 'ar' ? data.ai_boundary_ar : data.ai_boundary_en],
    [lang === 'ar' ? 'بحث الخريطة' : 'Map search', lang === 'ar' ? data.geocoder_note_ar : data.geocoder_note_en],
  ];
  $('dataCards').innerHTML = cards.map(([label,value]) => `<article><span>${esc(label)}</span><strong>${esc(value ?? '--')}</strong></article>`).join('');
  const sources = metadata.data_sources || [];
  $('dataSourceList').innerHTML = sources.map((src) => `<li><b>${esc(src.label)}</b><small>${esc(src.url)}</small></li>`).join('');
}
async function loadBootData() {
  try {
    const [health, locations, routes, quality] = await Promise.all([getJson('/api/health'), getJson('/api/locations'), getJson('/api/routes'), getJson('/api/data-quality')]);
    cachedRoutes = routes.routes || [];
    setStatus(`${t('ready')} · ${health.routes} ${lang === 'ar' ? 'اتجاه' : 'directions'} · ${health.trips} ${lang === 'ar' ? 'رحلة' : 'trips'}`);
    populateLocations(locations.locations || []);
    renderDataQuality(quality);
  } catch (error) {
    setStatus(error.message);
  }
}
function wireEvents() {
  $('departureTime').value = nowForDateTimeInput();
  $('langToggle').addEventListener('click', () => { lang = lang === 'ar' ? 'en' : 'ar'; applyLanguage(); });
  $('aiBtn').addEventListener('click', openVoice);
  $('closeAiDialog').addEventListener('click', () => $('aiDialog').close());
  $('sendChatBtn').addEventListener('click', sendChatMessage);
  $('chatInput').addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); } });
  $('useLocationBtn').addEventListener('click', usePreciseLocation);
  $('pickOriginBtn').addEventListener('click', () => setPicker('origin'));
  $('pickDestinationBtn').addEventListener('click', () => setPicker('destination'));
  $('origin').addEventListener('input', () => { if (originCoords) clearOriginCoordinateSelection(); });
  $('destination').addEventListener('input', () => { if (destinationCoords) clearDestinationCoordinateSelection(); });
  $('origin').addEventListener('change', maybeAutoRoute);
  $('destination').addEventListener('change', maybeAutoRoute);
  $('origin').addEventListener('keydown', (e) => { if (e.key === 'Enter') maybeAutoRoute(); });
  $('destination').addEventListener('keydown', (e) => { if (e.key === 'Enter') maybeAutoRoute(); });
  $('departureTime').addEventListener('change', maybeAutoRoute);
  $('areaForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const origin = $('areaOrigin').value.trim();
    const destination = $('areaDestination').value.trim();
    if (!origin || !destination) return;
    $('origin').value = origin; $('destination').value = destination; originCoords = null; destinationCoords = null;
    submitRoute({origin, destination, departure_time:$('departureTime').value, language:lang, priority:'lowest_cost'}, '/api/route');
  });
  $('alertBtn').addEventListener('click', toggleExitAlert);
  $('tripFeedback').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentRoute) return;
    const rating = new FormData($('tripFeedback')).get('rating') || 5;
    const routeIds = currentRoute.bus_routes || [];
    const payload = {rating, route_ids: routeIds, origin: currentRoute.origin?.name, destination: currentRoute.destination?.name, note: $('tripNote').value};
    try {
      const data = await postJson('/api/trip-feedback', payload);
      $('feedbackStatus').textContent = lang === 'ar' ? (data.message_ar || t('feedbackSaved')) : (data.message_en || t('feedbackSaved'));
    } catch (error) {
      $('feedbackStatus').textContent = error.message;
    }
  });
}

window.addEventListener('resize', () => { setMobileViewportHeight(); safeInvalidateMap(); });
window.addEventListener('orientationchange', () => { setMobileViewportHeight(); setTimeout(safeInvalidateMap, 250); setTimeout(safeInvalidateMap, 900); });
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', () => { setMobileViewportHeight(); safeInvalidateMap(); });
  window.visualViewport.addEventListener('scroll', () => { setMobileViewportHeight(); safeInvalidateMap(); });
}

window.addEventListener('DOMContentLoaded', () => {
  setMobileViewportHeight();
  initMap();
  wireEvents();
  setupVoice();
  applyLanguage();
  loadBootData();
  setTimeout(safeInvalidateMap, 300);
  setTimeout(safeInvalidateMap, 1200);
});
