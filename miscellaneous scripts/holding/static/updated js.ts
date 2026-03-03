
        // --- Three.js Scene Setup ---
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.getElementById('canvas-container').appendChild(renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7); 
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.9);
        directionalLight.position.set(15, 20, 10); 
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048; 
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        scene.add(directionalLight);
        
        // --- Ghana Map from GeoJSON ---
        let ghanaMapGroup; 
        const GEOJSON_FILE_NAME = 'ghana_regions.json'; 

        async function loadAndCreateGhanaMap() {
            let geoJsonPath;
            try {
                geoJsonPath = new URL(GEOJSON_FILE_NAME, window.location.href).href;
                console.log(`Attempting to fetch GeoJSON from: ${geoJsonPath}`);
                const response = await fetch(geoJsonPath);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} when fetching ${geoJsonPath}`);
                }
                const geoJsonData = await response.json();
                createGhanaMapFromGeoJSON(geoJsonData);
            } catch (error) {
                console.error(`Could not load or parse GeoJSON data from ${geoJsonPath || GEOJSON_FILE_NAME}:`, error);
                createFallbackMap();
            }
        }

        function createFallbackMap() {
            console.warn("Creating fallback map due to GeoJSON loading error.");
            ghanaMapGroup = new THREE.Group(); 
            const fallbackMaterial = new THREE.MeshPhongMaterial({ color: 0x555555 });
            const fallbackGeom = new THREE.BoxGeometry(5,0.5,5);
            const fallbackMesh = new THREE.Mesh(fallbackGeom, fallbackMaterial);
            fallbackMesh.position.y = -0.5;
            ghanaMapGroup.add(fallbackMesh);
            scene.add(ghanaMapGroup);
        }


        function createGhanaMapFromGeoJSON(geoJsonData) {
            if (!geoJsonData || !geoJsonData.features || geoJsonData.features.length === 0) {
                console.error("GeoJSON data is empty or invalid.");
                createFallbackMap();
                return;
            }

            ghanaMapGroup = new THREE.Group();
            const regionMaterial = new THREE.MeshPhongMaterial({
                color: 0x006A4E, 
                shininess: 15,
                side: THREE.DoubleSide,
            });
            const outlineMaterial = new THREE.LineBasicMaterial({ color: 0xFCD116, linewidth: 2 }); 

            const allPoints = [];
            geoJsonData.features.forEach(feature => {
                if (feature.geometry && feature.geometry.coordinates) {
                    const polygons = feature.geometry.type === 'Polygon' 
                        ? [feature.geometry.coordinates] 
                        : feature.geometry.coordinates;

                    polygons.forEach(polygonCoordsArray => {
                        const exteriorRing = polygonCoordsArray[0];
                        if (exteriorRing && exteriorRing.length > 0) {
                            exteriorRing.forEach(coord => {
                                if (coord && typeof coord[0] === 'number' && typeof coord[1] === 'number') {
                                    allPoints.push(new THREE.Vector2(coord[0], coord[1]));
                                } else {
                                    console.warn("Invalid coordinate found in GeoJSON:", coord, "Feature:", feature.properties.region);
                                }
                            });
                        }
                    });
                }
            });

            if (allPoints.length === 0) {
                console.error("No valid coordinates found in GeoJSON features to create map.");
                createFallbackMap();
                return;
            }

            const boundingBox = new THREE.Box2().setFromPoints(allPoints);
            const center = boundingBox.getCenter(new THREE.Vector2());
            const size = boundingBox.getSize(new THREE.Vector2());
            
            const maxDim = Math.max(size.x, size.y);
            const sceneScaleFactor = maxDim > 0 ? (10 / maxDim) : 1; 

            geoJsonData.features.forEach(feature => {
                if (feature.geometry && feature.geometry.coordinates) {
                    const polygons = feature.geometry.type === 'Polygon' 
                        ? [feature.geometry.coordinates]
                        : feature.geometry.coordinates;

                    polygons.forEach((polygonCoordsArray, polyIndex) => {
                        const exteriorRingCoords = polygonCoordsArray[0];
                        if (!exteriorRingCoords || exteriorRingCoords.length < 3) {
                            console.warn("Skipping invalid exterior ring for region:", feature.properties.region, "Polygon index:", polyIndex);
                            return; 
                        }

                        const regionShape = new THREE.Shape();
                        const firstPoint = exteriorRingCoords[0];
                        if (!firstPoint || typeof firstPoint[0] !== 'number' || typeof firstPoint[1] !== 'number') {
                             console.warn("Skipping shape due to invalid first point for region:", feature.properties.region);
                             return;
                        }
                        regionShape.moveTo(
                            (firstPoint[0] - center.x) * sceneScaleFactor,
                            (firstPoint[1] - center.y) * sceneScaleFactor
                        );

                        for (let i = 1; i < exteriorRingCoords.length; i++) {
                            const point = exteriorRingCoords[i];
                             if (!point || typeof point[0] !== 'number' || typeof point[1] !== 'number') {
                                console.warn("Skipping point due to invalid coordinate for region:", feature.properties.region);
                                continue;
                            }
                            regionShape.lineTo(
                                (point[0] - center.x) * sceneScaleFactor,
                                (point[1] - center.y) * sceneScaleFactor
                            );
                        }

                        for (let h = 1; h < polygonCoordsArray.length; h++) {
                            const holeCoords = polygonCoordsArray[h];
                             if (!holeCoords || holeCoords.length < 3) continue;

                            const holePath = new THREE.Path();
                            const firstHolePoint = holeCoords[0];
                            if (!firstHolePoint || typeof firstHolePoint[0] !== 'number' || typeof firstHolePoint[1] !== 'number') continue;

                            holePath.moveTo(
                                (firstHolePoint[0] - center.x) * sceneScaleFactor,
                                (firstHolePoint[1] - center.y) * sceneScaleFactor
                            );
                            for (let i = 1; i < holeCoords.length; i++) {
                                const holePoint = holeCoords[i];
                                if (!holePoint || typeof holePoint[0] !== 'number' || typeof holePoint[1] !== 'number') continue;
                                holePath.lineTo(
                                    (holePoint[0] - center.x) * sceneScaleFactor,
                                    (holePoint[1] - center.y) * sceneScaleFactor
                                );
                            }
                            regionShape.holes.push(holePath);
                        }


                        const extrudeSettings = {
                            steps: 1,
                            depth: 0.3, 
                            bevelEnabled: true,
                            bevelThickness: 0.05,
                            bevelSize: 0.05,
                            bevelOffset: 0,
                            bevelSegments: 1
                        };

                        const geometry = new THREE.ExtrudeGeometry(regionShape, extrudeSettings);
                        
                        const regionMesh = new THREE.Mesh(geometry, regionMaterial.clone()); 
                        regionMesh.castShadow = true;
                        regionMesh.receiveShadow = true;
                        regionMesh.name = feature.properties.region || `region-${polyIndex}`; 
                        ghanaMapGroup.add(regionMesh);

                        const edgesGeom = new THREE.EdgesGeometry(geometry);
                        const regionOutline = new THREE.LineSegments(edgesGeom, outlineMaterial.clone());
                        ghanaMapGroup.add(regionOutline);
                    });
                }
            });

            ghanaMapGroup.rotation.x = -Math.PI / 2; 
            ghanaMapGroup.position.y = -0.5; 
            scene.add(ghanaMapGroup);
            console.log("Ghana map created from GeoJSON data.");
        }

        loadAndCreateGhanaMap(); 

        let currentWeatherEffect = null; 

        camera.position.set(0, 10, 15); 
        camera.lookAt(0,0,0); 

        // --- UI Interaction & Data Handling (Flask Integration) ---
        const sourceButtons = document.querySelectorAll('.source-button');
        const capXmlInput = document.getElementById('cap-xml-input');
        const submitCapXmlButton = document.getElementById('submit-cap-xml');
        const capInputArea = document.getElementById('cap-input-area');

        const weatherAdvisoryEl = document.getElementById('weather-advisory');
        const agroAdvisoryEl = document.getElementById('agro-advisory');
        const capDisplayEl = document.getElementById('cap-alert-display');
        const weatherIconEl = weatherAdvisoryEl.querySelector('.advisory-icon');


        function showLoading(button, panelId) {
            if(button) button.classList.add('loading');
            const panel = document.getElementById(panelId);
            if (panel) {
                const p = panel.querySelector('p');
                if(p) p.textContent = 'Fetching data...';
                const h3 = panel.querySelector('h3#cap-headline'); 
                if(h3) h3.textContent = 'Processing CAP...';
            }
        }

        function hideLoading(button) {
            if(button) button.classList.remove('loading');
        }
        
        function updateUI(sourceKey, data) {
            console.log("Updating UI for:", sourceKey, "with data:", data);
            
            weatherAdvisoryEl.style.display = 'none';
            agroAdvisoryEl.style.display = 'none';
            capDisplayEl.style.display = 'none';
            capInputArea.style.display = 'none'; 

            if (data && data.error) {
                console.error("Error from backend:", data.error);
                let errorText = data.advisory_text || data.error || "An unknown error occurred.";
                if (sourceKey === 'meteo') {
                    weatherAdvisoryEl.style.display = 'block';
                    document.getElementById('weather-text').textContent = `Error: ${errorText}`;
                    if(weatherIconEl) weatherIconEl.textContent = '⚠️';
                } else if (sourceKey === 'agro') {
                    agroAdvisoryEl.style.display = 'block';
                    document.getElementById('agro-text').textContent = `Error: ${errorText}`;
                } else if (sourceKey === 'cap') {
                    capDisplayEl.style.display = 'block';
                    document.getElementById('cap-headline').textContent = 'CAP Processing Error';
                    document.getElementById('cap-description').textContent = errorText;
                }
                return; 
            }

            // If no error, proceed to update with data
            if (sourceKey === 'meteo' && data && data.advisory_text) {
                weatherAdvisoryEl.style.display = 'block';
                document.getElementById('weather-text').textContent = data.advisory_text;
                if(weatherIconEl && data.icon_emoji) weatherIconEl.textContent = data.icon_emoji;
            } else if (sourceKey === 'agro' && data && data.advisory_text) {
                agroAdvisoryEl.style.display = 'block';
                document.getElementById('agro-text').textContent = data.advisory_text;
            } else if (sourceKey === 'cap_input') { 
                capInputArea.style.display = 'block';
            } else if (sourceKey === 'cap' && data && data.headline) {
                capDisplayEl.style.display = 'block';
                document.getElementById('cap-headline').textContent = data.headline;
                document.getElementById('cap-description').textContent = data.description;
                document.getElementById('cap-area').textContent = `Area: ${data.area_description || 'N/A'}`;
                document.getElementById('cap-sender').textContent = `Sender: ${data.sender || 'N/A'}`;
                document.getElementById('cap-sent-time').textContent = `Sent: ${data.sent_time_cap ? new Date(data.sent_time_cap).toLocaleString() : 'N/A'}`;
            }
            
            // Example: Update status bar if data contains such fields
            // document.getElementById('active-alerts').textContent = data.alerts_count || 0;

            gsap.fromTo('.advisory-card:not([style*="display: none"])', {opacity: 0, y:20}, {opacity:1, y:0, duration:0.5, stagger:0.1});
        }
        
        sourceButtons.forEach(button => {
            if (button.disabled) return; // Skip disabled buttons

            button.addEventListener('click', async () => {
                const source = button.dataset.source;
                sourceButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                weatherAdvisoryEl.style.display = 'none';
                agroAdvisoryEl.style.display = 'none';
                capDisplayEl.style.display = 'none';
                capInputArea.style.display = 'none';

                if (source === 'cap') { 
                    updateUI('cap_input', {}); 
                    return; 
                }
                
                let panelIdToLoad = '';
                if (source === 'meteo') panelIdToLoad = 'weather-advisory';
                else if (source === 'agro') panelIdToLoad = 'agro-advisory';

                showLoading(button, panelIdToLoad);

                try {
                    const response = await fetch(`/fetch_data?source=${source}`); // Fetch from Flask backend
                    hideLoading(button); // Hide loading once response starts processing
                    if (!response.ok) {
                        let errorData;
                        try {
                            errorData = await response.json();
                        } catch (e) {
                            errorData = { error: `HTTP error ${response.status}. Could not parse error response.` };
                        }
                        throw new Error(errorData.advisory_text || errorData.error || `HTTP error ${response.status}`);
                    }
                    const data = await response.json();
                    updateUI(source, data);
                } catch (error) {
                    console.error(`Error fetching ${source} data:`, error);
                    hideLoading(button);
                    updateUI(source, { error: error.message, advisory_text: `Failed to load ${source} data. Server might be down or an error occurred.` });
                }
            });
        });

        if (submitCapXmlButton) {
            submitCapXmlButton.addEventListener('click', async () => {
                const capXml = capXmlInput.value;
                if (!capXml.trim()) {
                    alert("Please paste CAP XML data into the text area.");
                    return;
                }
                
                showLoading(null, 'cap-alert-display'); 
                capInputArea.style.display = 'none'; 

                try {
                    const response = await fetch('/submit_cap', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/xml' }, 
                        body: capXml
                    });
                     if (!response.ok) {
                        let errorData;
                        try {
                            errorData = await response.json();
                        } catch(e){
                             errorData = { error: `HTTP error ${response.status}. Could not parse error response.`};
                        }
                        throw new Error(errorData.advisory_text || errorData.error || `HTTP error ${response.status}`);
                    }
                    const data = await response.json();
                    updateUI('cap', data); 
                } catch (error) {
                    console.error('Error submitting CAP XML:', error);
                    updateUI('cap', { error: error.message, advisory_text: 'Failed to process CAP alert.' });
                } 
            });
        }


        function animate() {
            requestAnimationFrame(animate);
            if (ghanaMapGroup) { 
                ghanaMapGroup.rotation.y += 0.001; 
            }
            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        animate(); 

        setTimeout(() => {
            document.getElementById('loading').classList.add('hidden');
            gsap.from('.header h1', { y: -50, opacity: 0, duration: 1, ease: 'power3.out' });
            gsap.from('.glass-card', { scale: 0.8, opacity: 0, duration: 0.8, stagger: 0.1, ease: 'power3.out', delay: 0.3 });
            
            weatherAdvisoryEl.style.display = 'block';
            document.getElementById('weather-text').textContent = "Select a data source or input a CAP alert.";
            agroAdvisoryEl.style.display = 'none';
            capDisplayEl.style.display = 'none';
            capInputArea.style.display = 'none';

        }, 1000);

 