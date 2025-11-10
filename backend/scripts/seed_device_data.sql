-- Device Attributes Sample Data
-- 主要機種のサイズ情報（手帳型ケース用）

-- iPhone系
INSERT INTO device_attributes (brand, device_name, size_category, attribute_value) VALUES
('iPhone', 'iPhone 15 Pro Max', 'i6s', 'Large'),
('iPhone', 'iPhone 15 Pro', 'i6', 'Standard'),
('iPhone', 'iPhone 15 Plus', 'i6s', 'Large'),
('iPhone', 'iPhone 15', 'i6', 'Standard'),
('iPhone', 'iPhone 14 Pro Max', 'i6s', 'Large'),
('iPhone', 'iPhone 14 Pro', 'i6', 'Standard'),
('iPhone', 'iPhone 14 Plus', 'i6s', 'Large'),
('iPhone', 'iPhone 14', 'i6', 'Standard'),
('iPhone', 'iPhone 13 Pro Max', 'i6s', 'Large'),
('iPhone', 'iPhone 13 Pro', 'i6', 'Standard'),
('iPhone', 'iPhone 13', 'i6', 'Standard'),
('iPhone', 'iPhone 13 mini', 'i5', 'Small'),
('iPhone', 'iPhone 12 Pro Max', 'i6s', 'Large'),
('iPhone', 'iPhone 12 Pro', 'i6', 'Standard'),
('iPhone', 'iPhone 12', 'i6', 'Standard'),
('iPhone', 'iPhone 12 mini', 'i5', 'Small'),
('iPhone', 'iPhone 11 Pro Max', 'i6s', 'Large'),
('iPhone', 'iPhone 11 Pro', 'i5s', 'Medium'),
('iPhone', 'iPhone 11', 'i6', 'Standard'),
('iPhone', 'iPhone XS Max', 'i6s', 'Large'),
('iPhone', 'iPhone XS', 'i5s', 'Medium'),
('iPhone', 'iPhone XR', 'i6', 'Standard'),
('iPhone', 'iPhone X', 'i5s', 'Medium'),
('iPhone', 'iPhone 8 Plus', 'i6', 'Standard'),
('iPhone', 'iPhone 8', 'i6', 'Standard'),
('iPhone', 'iPhone 7 Plus', 'i6', 'Standard'),
('iPhone', 'iPhone 7', 'i6', 'Standard'),
('iPhone', 'iPhone SE (第3世代)', 'i6', 'Standard'),
('iPhone', 'iPhone SE (第2世代)', 'i6', 'Standard');

-- Galaxy系
INSERT INTO device_attributes (brand, device_name, size_category, attribute_value) VALUES
('Galaxy', 'Galaxy S23 Ultra', 'L', 'Large'),
('Galaxy', 'Galaxy S23+', 'L', 'Large'),
('Galaxy', 'Galaxy S23', 'M', 'Medium'),
('Galaxy', 'Galaxy S22 Ultra', 'L', 'Large'),
('Galaxy', 'Galaxy S22+', 'L', 'Large'),
('Galaxy', 'Galaxy S22', 'M', 'Medium'),
('Galaxy', 'Galaxy S21 Ultra', 'L', 'Large'),
('Galaxy', 'Galaxy S21+', 'L', 'Large'),
('Galaxy', 'Galaxy S21', 'M', 'Medium'),
('Galaxy', 'Galaxy A54', 'M', 'Medium'),
('Galaxy', 'Galaxy A53', 'M', 'Medium'),
('Galaxy', 'Galaxy A52', 'M', 'Medium'),
('Galaxy', 'Galaxy A23', 'M', 'Medium'),
('Galaxy', 'Galaxy A22', 'M', 'Medium'),
('Galaxy', 'Galaxy Z Fold5', '特大', 'Extra Large'),
('Galaxy', 'Galaxy Z Fold4', '特大', 'Extra Large'),
('Galaxy', 'Galaxy Z Flip5', 'M', 'Medium'),
('Galaxy', 'Galaxy Z Flip4', 'M', 'Medium');

-- AQUOS系
INSERT INTO device_attributes (brand, device_name, size_category, attribute_value) VALUES
('AQUOS', 'AQUOS wish4', 'M', 'Medium'),
('AQUOS', 'AQUOS wish3', 'M', 'Medium'),
('AQUOS', 'AQUOS wish2', 'M', 'Medium'),
('AQUOS', 'AQUOS wish', 'M', 'Medium'),
('AQUOS', 'AQUOS sense8', 'M', 'Medium'),
('AQUOS', 'AQUOS sense7', 'M', 'Medium'),
('AQUOS', 'AQUOS sense7 plus', 'L', 'Large'),
('AQUOS', 'AQUOS sense6', 'M', 'Medium'),
('AQUOS', 'AQUOS sense5G', 'M', 'Medium'),
('AQUOS', 'AQUOS sense4', 'M', 'Medium'),
('AQUOS', 'AQUOS R8 pro', 'L', 'Large'),
('AQUOS', 'AQUOS R8', 'M', 'Medium'),
('AQUOS', 'AQUOS R7', 'L', 'Large'),
('AQUOS', 'AQUOS R6', 'L', 'Large'),
('AQUOS', 'AQUOS zero6', 'M', 'Medium'),
('AQUOS', 'AQUOS We2', 'M', 'Medium'),
('AQUOS', 'AQUOS We', 'M', 'Medium');

-- Xperia系
INSERT INTO device_attributes (brand, device_name, size_category, attribute_value) VALUES
('Xperia', 'Xperia 1 V', 'L', 'Large'),
('Xperia', 'Xperia 1 IV', 'L', 'Large'),
('Xperia', 'Xperia 1 III', 'L', 'Large'),
('Xperia', 'Xperia 5 V', 'M', 'Medium'),
('Xperia', 'Xperia 5 IV', 'M', 'Medium'),
('Xperia', 'Xperia 5 III', 'M', 'Medium'),
('Xperia', 'Xperia 10 V', 'M', 'Medium'),
('Xperia', 'Xperia 10 IV', 'M', 'Medium'),
('Xperia', 'Xperia 10 III', 'M', 'Medium'),
('Xperia', 'Xperia Ace III', 'S', 'Small'),
('Xperia', 'Xperia Ace II', 'S', 'Small');

-- Pixel系
INSERT INTO device_attributes (brand, device_name, size_category, attribute_value) VALUES
('Pixel', 'Pixel 8 Pro', 'L', 'Large'),
('Pixel', 'Pixel 8', 'M', 'Medium'),
('Pixel', 'Pixel 7 Pro', 'L', 'Large'),
('Pixel', 'Pixel 7', 'M', 'Medium'),
('Pixel', 'Pixel 7a', 'M', 'Medium'),
('Pixel', 'Pixel 6 Pro', 'L', 'Large'),
('Pixel', 'Pixel 6', 'M', 'Medium'),
('Pixel', 'Pixel 6a', 'M', 'Medium'),
('Pixel', 'Pixel 5', 'M', 'Medium'),
('Pixel', 'Pixel 4a', 'M', 'Medium');

-- その他主要ブランド
INSERT INTO device_attributes (brand, device_name, size_category, attribute_value) VALUES
('OPPO', 'OPPO Reno10 Pro 5G', 'M', 'Medium'),
('OPPO', 'OPPO Reno9 A', 'M', 'Medium'),
('OPPO', 'OPPO A79 5G', 'M', 'Medium'),
('OPPO', 'OPPO A77', 'M', 'Medium'),
('Xiaomi', 'Xiaomi 13T Pro', 'L', 'Large'),
('Xiaomi', 'Xiaomi 13T', 'M', 'Medium'),
('Xiaomi', 'Redmi Note 13 Pro 5G', 'M', 'Medium'),
('Xiaomi', 'Redmi 12 5G', 'M', 'Medium'),
('arrows', 'arrows We', 'M', 'Medium'),
('arrows', 'arrows N', 'M', 'Medium'),
('arrows', 'arrows BZ01', 'M', 'Medium');

-- 集計: 合計約90機種のサイズ情報を登録
