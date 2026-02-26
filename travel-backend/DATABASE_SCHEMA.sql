-- Club Luxora Travel Platform Database Schema
-- PostgreSQL Database Schema

-- ============================================
-- DESTINATIONS
-- ============================================

CREATE TABLE destinations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    destination_type VARCHAR(20) NOT NULL CHECK (destination_type IN ('kerala', 'international')),
    subtitle VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(200) NOT NULL,
    main_image VARCHAR(255) NOT NULL,
    thumbnail VARCHAR(255),
    tour_count INTEGER DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    is_trending BOOLEAN DEFAULT FALSE,
    is_popular BOOLEAN DEFAULT FALSE,
    is_top_destination BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE INDEX idx_destinations_type ON destinations(destination_type);
CREATE INDEX idx_destinations_trending ON destinations(is_trending);
CREATE INDEX idx_destinations_popular ON destinations(is_popular);

-- ============================================
-- PACKAGES
-- ============================================

CREATE TABLE packages (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE NOT NULL,
    package_type VARCHAR(20) NOT NULL CHECK (package_type IN ('kerala', 'international')),
    category VARCHAR(50) NOT NULL,
    season VARCHAR(20) DEFAULT 'all',
    destination_id INTEGER REFERENCES destinations(id) ON DELETE CASCADE,
    location VARCHAR(200) NOT NULL,
    duration_days INTEGER NOT NULL,
    duration_nights INTEGER NOT NULL,
    group_size_min INTEGER DEFAULT 2,
    group_size_max INTEGER DEFAULT 10,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    price_per_night DECIMAL(10, 2),
    description TEXT NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    main_image VARCHAR(255) NOT NULL,
    hero_image VARCHAR(255),
    rating DECIMAL(3, 2) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_trending BOOLEAN DEFAULT FALSE,
    is_popular BOOLEAN DEFAULT FALSE,
    is_best_seller BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    meta_title VARCHAR(200),
    meta_description VARCHAR(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_packages_type ON packages(package_type);
CREATE INDEX idx_packages_category ON packages(category);
CREATE INDEX idx_packages_season ON packages(season);
CREATE INDEX idx_packages_featured ON packages(is_featured);
CREATE INDEX idx_packages_trending ON packages(is_trending);
CREATE INDEX idx_packages_active ON packages(is_active);
CREATE INDEX idx_packages_price ON packages(price);


-- ============================================
-- PACKAGE RELATED TABLES
-- ============================================

CREATE TABLE package_gallery (
    id SERIAL PRIMARY KEY,
    package_id INTEGER REFERENCES packages(id) ON DELETE CASCADE,
    image VARCHAR(255) NOT NULL,
    caption VARCHAR(200),
    "order" INTEGER DEFAULT 0
);

CREATE INDEX idx_package_gallery_package ON package_gallery(package_id);

CREATE TABLE package_inclusions (
    id SERIAL PRIMARY KEY,
    package_id INTEGER REFERENCES packages(id) ON DELETE CASCADE,
    item VARCHAR(300) NOT NULL,
    "order" INTEGER DEFAULT 0
);

CREATE INDEX idx_package_inclusions_package ON package_inclusions(package_id);

CREATE TABLE package_exclusions (
    id SERIAL PRIMARY KEY,
    package_id INTEGER REFERENCES packages(id) ON DELETE CASCADE,
    item VARCHAR(300) NOT NULL,
    "order" INTEGER DEFAULT 0
);

CREATE INDEX idx_package_exclusions_package ON package_exclusions(package_id);

CREATE TABLE package_itinerary (
    id SERIAL PRIMARY KEY,
    package_id INTEGER REFERENCES packages(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    activities TEXT,
    meals_included VARCHAR(100)
);

CREATE INDEX idx_package_itinerary_package ON package_itinerary(package_id);

CREATE TABLE package_amenities (
    id SERIAL PRIMARY KEY,
    package_id INTEGER REFERENCES packages(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50) NOT NULL
);

CREATE INDEX idx_package_amenities_package ON package_amenities(package_id);

-- ============================================
-- HOTELS
-- ============================================

CREATE TABLE hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE NOT NULL,
    hotel_type VARCHAR(50) NOT NULL,
    location VARCHAR(200) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    star_rating INTEGER CHECK (star_rating BETWEEN 1 AND 5),
    price_per_night DECIMAL(10, 2) NOT NULL,
    main_image VARCHAR(255) NOT NULL,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hotels_type ON hotels(hotel_type);
CREATE INDEX idx_hotels_city ON hotels(city);
CREATE INDEX idx_hotels_active ON hotels(is_active);

CREATE TABLE hotel_amenities (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER REFERENCES hotels(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50) NOT NULL
);

CREATE INDEX idx_hotel_amenities_hotel ON hotel_amenities(hotel_id);

-- ============================================
-- HOUSEBOATS
-- ============================================

CREATE TABLE houseboats (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE NOT NULL,
    houseboat_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    route VARCHAR(200) NOT NULL,
    capacity_min INTEGER NOT NULL,
    capacity_max INTEGER NOT NULL,
    bedrooms INTEGER NOT NULL,
    price_per_night DECIMAL(10, 2) NOT NULL,
    price_day_cruise DECIMAL(10, 2),
    main_image VARCHAR(255) NOT NULL,
    has_ac BOOLEAN DEFAULT TRUE,
    has_sundeck BOOLEAN DEFAULT TRUE,
    meals_included BOOLEAN DEFAULT TRUE,
    private_chef BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_houseboats_type ON houseboats(houseboat_type);
CREATE INDEX idx_houseboats_active ON houseboats(is_active);

-- ============================================
-- CRUISES
-- ============================================

CREATE TABLE cruises (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE NOT NULL,
    cruise_line VARCHAR(200) NOT NULL,
    route VARCHAR(300) NOT NULL,
    departure_port VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    duration_nights INTEGER NOT NULL,
    price_per_person DECIMAL(10, 2) NOT NULL,
    main_image VARCHAR(255) NOT NULL,
    departure_months VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cruises_active ON cruises(is_active);

CREATE TABLE cruise_highlights (
    id SERIAL PRIMARY KEY,
    cruise_id INTEGER REFERENCES cruises(id) ON DELETE CASCADE,
    highlight VARCHAR(200) NOT NULL,
    "order" INTEGER DEFAULT 0
);

CREATE INDEX idx_cruise_highlights_cruise ON cruise_highlights(cruise_id);

-- ============================================
-- ISLAND STAYS
-- ============================================

CREATE TABLE island_stays (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE NOT NULL,
    location VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    duration_nights INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    main_image VARCHAR(255) NOT NULL,
    star_rating INTEGER CHECK (star_rating BETWEEN 1 AND 5),
    rating DECIMAL(3, 2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_island_stays_active ON island_stays(is_active);

CREATE TABLE island_stay_features (
    id SERIAL PRIMARY KEY,
    island_stay_id INTEGER REFERENCES island_stays(id) ON DELETE CASCADE,
    feature VARCHAR(200) NOT NULL
);

CREATE INDEX idx_island_stay_features_island ON island_stay_features(island_stay_id);


-- ============================================
-- SERVICES
-- ============================================

CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    short_description VARCHAR(300) NOT NULL,
    icon VARCHAR(50) NOT NULL,
    image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_services_type ON services(service_type);
CREATE INDEX idx_services_active ON services(is_active);

-- ============================================
-- ENQUIRIES
-- ============================================

CREATE TABLE enquiries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    service VARCHAR(50) NOT NULL,
    destination VARCHAR(200),
    travel_date DATE,
    travelers VARCHAR(20),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'new',
    assigned_to_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    referrer VARCHAR(2000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_enquiries_status ON enquiries(status);
CREATE INDEX idx_enquiries_service ON enquiries(service);
CREATE INDEX idx_enquiries_created ON enquiries(created_at);
CREATE INDEX idx_enquiries_email ON enquiries(email);

-- ============================================
-- FLIGHT ENQUIRIES
-- ============================================

CREATE TABLE flight_enquiries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    trip_type VARCHAR(20) NOT NULL,
    from_location VARCHAR(200) NOT NULL,
    to_location VARCHAR(200) NOT NULL,
    departure_date DATE NOT NULL,
    return_date DATE,
    adults INTEGER DEFAULT 1,
    children INTEGER DEFAULT 0,
    travel_class VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flight_enquiries_status ON flight_enquiries(status);
CREATE INDEX idx_flight_enquiries_created ON flight_enquiries(created_at);

-- ============================================
-- NEWSLETTER
-- ============================================

CREATE TABLE newsletter (
    id SERIAL PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    name VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_newsletter_active ON newsletter(is_active);
CREATE INDEX idx_newsletter_subscribed ON newsletter(subscribed_at);

-- ============================================
-- TESTIMONIALS
-- ============================================

CREATE TABLE testimonials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    location VARCHAR(200) NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    testimonial TEXT NOT NULL,
    image VARCHAR(255),
    video_url VARCHAR(2000),
    package_id INTEGER REFERENCES packages(id) ON DELETE SET NULL,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_testimonials_featured ON testimonials(is_featured);
CREATE INDEX idx_testimonials_active ON testimonials(is_active);
CREATE INDEX idx_testimonials_package ON testimonials(package_id);

-- ============================================
-- SAMPLE DATA INSERTS
-- ============================================

-- Insert Kerala Destinations
INSERT INTO destinations (name, slug, destination_type, subtitle, description, location, main_image, tour_count, rating, is_trending, is_popular) VALUES
('Alleppey', 'alleppey', 'kerala', 'Backwaters', 'Famous for its backwaters and houseboat cruises', 'Kerala, India', 'destinations/alleppey.jpg', 24, 4.8, TRUE, TRUE),
('Munnar', 'munnar', 'kerala', 'Hill Station', 'Tea plantations and misty mountains', 'Kerala, India', 'destinations/munnar.jpg', 20, 4.7, TRUE, FALSE),
('Fort Kochi', 'fort-kochi', 'kerala', 'Heritage', 'Colonial architecture and cultural heritage', 'Kerala, India', 'destinations/kochi.jpg', 15, 4.6, FALSE, TRUE);

-- Insert International Destinations
INSERT INTO destinations (name, slug, destination_type, subtitle, description, location, main_image, tour_count, rating, is_trending, is_popular) VALUES
('Maldives', 'maldives', 'international', 'Beach Paradise', 'Crystal clear waters and luxury resorts', 'Maldives', 'destinations/maldives.jpg', 32, 4.9, TRUE, TRUE),
('Switzerland', 'switzerland', 'international', 'Mountains', 'Alpine beauty and scenic landscapes', 'Switzerland', 'destinations/swiss.jpg', 28, 4.9, TRUE, FALSE),
('Dubai', 'dubai', 'international', 'Luxury City', 'Modern architecture and desert adventures', 'UAE', 'destinations/dubai.jpg', 22, 4.8, FALSE, TRUE);

-- Insert Sample Packages
INSERT INTO packages (title, slug, package_type, category, season, destination_id, location, duration_days, duration_nights, price, original_price, description, short_description, main_image, rating, review_count, is_featured, is_trending, is_best_seller) VALUES
('Kerala Backwater Bliss', 'kerala-backwater-bliss', 'kerala', 'holiday', 'all', 1, 'Alleppey, Kerala', 3, 2, 24999.00, 29999.00, 'Experience the serene beauty of Kerala backwaters', 'Luxury houseboat cruise through palm-fringed canals', 'packages/backwater.jpg', 4.8, 124, FALSE, TRUE, TRUE),
('Maldives Paradise Getaway', 'maldives-paradise-getaway', 'international', 'beach', 'winter', 4, 'Maldives', 5, 4, 89999.00, 110000.00, 'Tropical paradise with overwater villas', 'Luxury beach resort with all-inclusive amenities', 'packages/maldives.jpg', 4.9, 203, TRUE, TRUE, TRUE);
