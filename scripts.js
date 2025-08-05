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

    // Toggle hamburger menu and handle aria attributes for accessibility
    hamburger.addEventListener('click', (event) => {
        event.stopPropagation();
        const isActive = navMenu.classList.toggle('active');
        hamburger.classList.toggle('active');
        hamburger.setAttribute('aria-expanded', isActive);
        document.body.style.overflow = isActive ? 'hidden' : ''; // Prevent scrolling when menu is open
        console.log("Hamburger clicked, active class toggled. Menu state:", isActive);
    });

    // Close menu when clicking nav links
    document.querySelectorAll('nav ul li a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
            hamburger.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = ''; // Restore scrolling
            console.log("Nav link clicked, menu closed");
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
        if (!navMenu.contains(event.target) && !hamburger.contains(event.target)) {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
            hamburger.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
            console.log("Clicked outside, menu closed");
        }
    });

    // Handle window resize for responsive menu behavior
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
            hamburger.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
            console.log("Window resized above 768px, menu reset");
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
