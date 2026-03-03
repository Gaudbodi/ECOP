// main.js
import * as THREE from 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js';
// Optional: For camera controls like OrbitControls
// import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/controls/OrbitControls.js';

let scene, camera, renderer, ghanaGroup;

function init() {
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222); // Dark background

    // Camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 1.5, 3); // Adjust based on map size and projection

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 10, 7.5);
    scene.add(directionalLight);

    // Group to hold all parts of Ghana for easier manipulation
    ghanaGroup = new THREE.Group();
    scene.add(ghanaGroup);

    // Optional: Orbit Controls
    // const controls = new OrbitControls(camera, renderer.domElement);
    // controls.enableDamping = true;

    // Load map data
    loadMapData();

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);

    animate();
}

async function loadMapData() {
    try {
        const response = await fetch('./ghana_towns.json'); // Ensure this path is correct
        if (!response.ok) throw new Error(`Failed to load GeoJSON: ${response.status}`);
        const geojsonData = await response.json();

        // Define a D3 projection
        // Fit the GeoJSON to a specific size in your 3D scene
        // These values [width, height] will determine the scale of your map.
        // You'll need to experiment with these and camera position.
        const projection = d3.geoMercator().fitSize([2, 2], geojsonData);

        const material = new THREE.MeshStandardMaterial({
            color: 0x00aa00, // Green color for Ghana
            metalness: 0.3,
            roughness: 0.7,
            side: THREE.DoubleSide // Render both sides
        });

        geojsonData.features.forEach(feature => {
            if (feature.geometry) {
                const type = feature.geometry.type;
                const coordinates = feature.geometry.coordinates;

                // Function to create shapes from polygon coordinates
                const createShapes = (polygonCoords) => {
                    const shape = new THREE.Shape();
                    polygonCoords.forEach((coord, index) => {
                        const [x, y] = projection(coord); // Project lon/lat to x/y
                        if (index === 0) {
                            shape.moveTo(x, y);
                        } else {
                            shape.lineTo(x, y);
                        }
                    });
                    return shape;
                };

                if (type === 'Polygon') {
                    coordinates.forEach(polygon => {
                        const shape = createShapes(polygon);
                        addExtrudedMesh(shape, material);
                    });
                } else if (type === 'MultiPolygon') {
                    coordinates.forEach(multiPoly => {
                        multiPoly.forEach(polygon => {
                            const shape = createShapes(polygon);
                            addExtrudedMesh(shape, material);
                        });
                    });
                }
            }
        });

        // Center the ghanaGroup and adjust its rotation/position if needed
        const box = new THREE.Box3().setFromObject(ghanaGroup);
        const center = box.getCenter(new THREE.Vector3());
        ghanaGroup.position.sub(center); // Center the group at the origin
        ghanaGroup.rotation.x = -Math.PI / 2; // Rotate to lay flat on XZ plane

        // Optional: GSAP animation after loading
        animateCameraWithGSAP();

    } catch (error) {
        console.error('Error loading or processing map data:', error);
    }
}

function addExtrudedMesh(shape, material) {
    const extrudeSettings = {
        steps: 1,
        depth: 0.1, // Thickness of the country
        bevelEnabled: false
    };
    const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    const mesh = new THREE.Mesh(geometry, material);
    ghanaGroup.add(mesh);
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    // Any continuous animations (e.g., group rotation)
    // ghanaGroup.rotation.y += 0.001; 
    renderer.render(scene, camera);
}

function animateCameraWithGSAP() {
    if (typeof gsap !== 'undefined') {
        gsap.fromTo(camera.position,
            { z: 10, y: 5 }, // Start position (further away and higher)
            {
                duration: 2.5,
                z: 2.5,        // End position (closer)
                y: 1,        // Slightly lower
                ease: "power3.inOut",
                onUpdate: () => {
                    camera.lookAt(ghanaGroup.position); // Keep looking at the map
                }
            }
        );

        // Example: Animate map appearing (scale or opacity)
        ghanaGroup.scale.set(0.1, 0.1, 0.1);
        gsap.to(ghanaGroup.scale, {
            duration: 1.5,
            x: 1,
            y: 1,
            z: 1,
            delay: 1, // Start after camera move begins
            ease: "elastic.out(1, 0.5)"
        });
    }
}

// Start everything
init();