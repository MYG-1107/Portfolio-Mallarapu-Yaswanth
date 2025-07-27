console.log("Script loaded");

document.addEventListener('DOMContentLoaded', () => {
    // Hamburger Menu Toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('#nav-menu');

    if (!hamburger || !navMenu) {
        console.error('Error: Hamburger or nav menu not found. Hamburger:', hamburger, 'NavMenu:', navMenu);
        return;
    }

    console.log("Hamburger and nav menu found, attaching event listener");

    hamburger.addEventListener('click', (event) => {
        event.stopPropagation();
        navMenu.classList.toggle('active');
        console.log("Hamburger clicked, active class toggled. Menu state:", navMenu.classList.contains('active'));
    });

    document.querySelectorAll('nav ul li a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            console.log("Nav link clicked, menu closed");
        });
    });

    document.addEventListener('click', (event) => {
        if (!navMenu.contains(event.target) && !hamburger.contains(event.target)) {
            navMenu.classList.remove('active');
            console.log("Clicked outside, menu closed");
        }
    });

    // Three.js 3D Background
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('three-canvas'), alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);

    const geometry = new THREE.TorusGeometry(10, 3, 16, 100);
    const material = new THREE.MeshBasicMaterial({ color: 0x08d9d6, wireframe: true });
    const torus = new THREE.Mesh(geometry, material);
    scene.add(torus);

    camera.position.z = 30;

    function animate() {
        requestAnimationFrame(animate);
        torus.rotation.x += 0.01;
        torus.rotation.y += 0.01;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
    });

    // GSAP Animations
    gsap.registerPlugin(ScrollTrigger);

    gsap.from('#hero .hero-content', {
        opacity: 0,
        y: 100,
        duration: 1.5,
        ease: 'power3.out'
    });

    document.querySelectorAll('section').forEach(section => {
        gsap.from(section, {
            opacity: 0,
            y: 50,
            duration: 1,
            scrollTrigger: {
                trigger: section,
                start: 'top 80%',
                toggleActions: 'play none none none'
            }
        });
    });

    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('mouseenter', () => {
            gsap.to(link, { scale: 1.1, duration: 0.3 });
        });
        link.addEventListener('mouseleave', () => {
            gsap.to(link, { scale: 1, duration: 0.3 });
        });
    });

    // Smooth Scrolling
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Disable Right-Click
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        alert('Right-click is disabled on this page.');
    });

    // Disable Copy
    document.addEventListener('copy', (event) => {
        event.preventDefault();
        alert('Copying is disabled on this webpage!');
    });
});