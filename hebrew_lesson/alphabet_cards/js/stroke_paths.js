/**
 * Hebrew Letter Stroke Paths
 * SVG path data for stroke order animations
 * ViewBox: 0 0 200 200
 *
 * Based on SBL Hebrew / Ezra SIL font glyph shapes.
 * Each stroke follows the visual contour of the actual rendered letter.
 *
 * COORDINATE SYSTEM:
 * - Origin (0,0) is top-left
 * - X increases rightward (0=left, 200=right)
 * - Y increases downward (0=top, 200=bottom)
 * - Letters centered, main body y=40-160, x=40-160
 *
 * STROKE ORDER (Hebrew Ktav Ashuri):
 * - Right to left
 * - Top before bottom
 * - Connected strokes together
 */

const strokePaths = {
    // ═══════════════════════════════════════════════════════════════════
    // א Aleph - Diagonal X-like shape
    // Upper-right arm curves down-left, small upper-left yod, lower diagonal leg
    // ═══════════════════════════════════════════════════════════════════
    "א": {
        strokes: [
            // Stroke 1: Upper-right arm - thick curved stroke from top-right curving down toward center
            { path: "M 148 60 Q 140 65 130 80 Q 120 95 112 108", desc: "1. 右上臂" },
            // Stroke 2: Upper-left yod - small comma-like stroke
            { path: "M 88 58 Q 78 62 76 75 Q 76 85 82 90", desc: "2. 左上點" },
            // Stroke 3: Lower diagonal leg - from center down to lower-left
            { path: "M 112 108 Q 100 125 85 145 Q 70 162 55 172", desc: "3. 左下腿" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ב Bet - Open box shape (open on left)
    // Roof + right leg + base with upturned foot
    // ═══════════════════════════════════════════════════════════════════
    "ב": {
        strokes: [
            // Stroke 1: Roof - slightly curved horizontal from right to left
            { path: "M 152 52 Q 120 48 85 50 Q 60 52 48 58", desc: "1. 頂橫" },
            // Stroke 2: Right leg - vertical with slight thickening
            { path: "M 148 52 L 148 158", desc: "2. 右豎" },
            // Stroke 3: Base going left then curving up into foot
            { path: "M 148 158 L 80 158 Q 62 158 62 145 L 62 130", desc: "3. 底及腳" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ג Gimel - Curved head flowing into stem with diagonal foot
    // ═══════════════════════════════════════════════════════════════════
    "ג": {
        strokes: [
            // Stroke 1: Head curves from right into vertical stem
            { path: "M 135 48 Q 118 46 112 55 Q 108 65 108 80 L 108 110", desc: "1. 頭及豎" },
            // Stroke 2: Diagonal foot going down-left
            { path: "M 108 110 Q 95 130 78 152 Q 62 170 48 178", desc: "2. 斜腳" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ד Dalet - Inverted L, roof extends past right leg
    // ═══════════════════════════════════════════════════════════════════
    "ד": {
        strokes: [
            // Stroke 1: Roof - extends well to the left
            { path: "M 152 52 Q 115 46 80 50 Q 55 54 42 62", desc: "1. 頂橫" },
            // Stroke 2: Right leg
            { path: "M 148 52 L 148 162", desc: "2. 右豎" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ה He - Roof with two legs, left leg detached from roof
    // ═══════════════════════════════════════════════════════════════════
    "ה": {
        strokes: [
            // Stroke 1: Roof
            { path: "M 156 52 Q 115 46 75 50 Q 50 54 38 62", desc: "1. 頂橫" },
            // Stroke 2: Right leg (attached)
            { path: "M 152 52 L 152 162", desc: "2. 右腿" },
            // Stroke 3: Left leg (detached, gap from roof)
            { path: "M 58 82 L 58 162", desc: "3. 左腿" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ו Vav - Head hook flowing into vertical
    // ═══════════════════════════════════════════════════════════════════
    "ו": {
        strokes: [
            // Single stroke: curved head then vertical
            { path: "M 118 48 Q 100 46 95 58 Q 92 70 92 85 L 92 162", desc: "1. 頭及豎" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ז Zayin - Crown/head on vertical stem
    // ═══════════════════════════════════════════════════════════════════
    "ז": {
        strokes: [
            // Stroke 1: Crown - horizontal with tapered ends
            { path: "M 128 52 Q 105 48 85 50 Q 68 54 58 60", desc: "1. 冠頂" },
            // Stroke 2: Vertical stem from center
            { path: "M 95 52 L 95 162", desc: "2. 豎幹" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ח Chet - Roof beam connecting two legs (both attached)
    // ═══════════════════════════════════════════════════════════════════
    "ח": {
        strokes: [
            // Stroke 1: Roof/beam
            { path: "M 158 52 Q 105 44 55 52 Q 42 56 38 62", desc: "1. 頂樑" },
            // Stroke 2: Right leg
            { path: "M 152 52 L 152 162", desc: "2. 右腿" },
            // Stroke 3: Left leg (attached via curved connection at top)
            { path: "M 48 58 L 48 162", desc: "3. 左腿" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ט Tet - Bowl with inward curl at bottom-right
    // ═══════════════════════════════════════════════════════════════════
    "ט": {
        strokes: [
            // Stroke 1: Left side up and across top
            { path: "M 48 162 L 48 85 Q 48 52 85 48 Q 105 46 125 48", desc: "1. 左及頂" },
            // Stroke 2: Right side down
            { path: "M 125 48 Q 152 50 155 75 L 155 120", desc: "2. 右下" },
            // Stroke 3: Inward curl
            { path: "M 155 120 Q 155 148 130 152 Q 105 154 95 145 Q 88 138 92 125", desc: "3. 內捲" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // י Yod - Small comma/apostrophe shape
    // ═══════════════════════════════════════════════════════════════════
    "י": {
        strokes: [
            // Single small curved stroke
            { path: "M 118 55 Q 98 52 95 68 Q 94 82 100 92 Q 108 98 115 94", desc: "1. 點" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // כ Kaf - C-shaped bowl, open on left
    // ═══════════════════════════════════════════════════════════════════
    "כ": {
        strokes: [
            // Single curved bowl stroke
            { path: "M 152 52 Q 130 46 95 48 Q 55 52 48 90 Q 45 125 55 152 Q 68 165 110 165 Q 145 162 152 130 L 152 52", desc: "1. 碗形" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ך Final Kaf - Curved roof with long descender
    // ═══════════════════════════════════════════════════════════════════
    "ך": {
        strokes: [
            // Stroke 1: Curved roof
            { path: "M 148 52 Q 110 44 72 50 Q 52 56 42 68", desc: "1. 頂弧" },
            // Stroke 2: Long descender below baseline
            { path: "M 145 52 L 145 190", desc: "2. 長豎" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ל Lamed - Tallest letter, ascending neck with hook
    // ═══════════════════════════════════════════════════════════════════
    "ל": {
        strokes: [
            // Single continuous stroke: base, up the neck, hook at top
            { path: "M 42 162 L 108 162 Q 145 162 148 125 L 148 35 Q 148 18 132 20 Q 118 24 120 42 Q 124 52 132 55", desc: "1. 底至頂鉤" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // מ Mem (open) - Frame with diagonal inner stroke
    // ═══════════════════════════════════════════════════════════════════
    "מ": {
        strokes: [
            // Stroke 1: Outer frame - right side, top curve, left side
            { path: "M 152 162 L 152 82 Q 152 52 115 48 L 88 48 Q 52 48 48 82 L 48 145", desc: "1. 外框" },
            // Stroke 2: Inner diagonal
            { path: "M 135 78 Q 118 108 95 140 Q 82 158 68 168", desc: "2. 內斜" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ם Final Mem - Closed rectangle
    // ═══════════════════════════════════════════════════════════════════
    "ם": {
        strokes: [
            // Single closed rectangle
            { path: "M 152 48 L 48 48 L 48 162 L 152 162 L 152 48", desc: "1. 方框" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // נ Nun - Head, vertical, curved base extending left
    // ═══════════════════════════════════════════════════════════════════
    "נ": {
        strokes: [
            // Single stroke: head hook, vertical, base curve left
            { path: "M 132 48 Q 112 46 108 60 Q 106 75 106 95 L 106 145 Q 106 162 82 162 L 42 162", desc: "1. 頭豎底" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ן Final Nun - Long vertical descender
    // ═══════════════════════════════════════════════════════════════════
    "ן": {
        strokes: [
            // Single stroke: head hook then long vertical
            { path: "M 118 48 Q 98 46 95 62 Q 93 78 93 95 L 93 190", desc: "1. 頭及長豎" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ס Samekh - Rounded rectangle/oval shape (closed)
    // Note: SBL Hebrew has more squared corners than a pure oval
    // ═══════════════════════════════════════════════════════════════════
    "ס": {
        strokes: [
            // Single closed shape - more rectangular than circular
            { path: "M 100 48 Q 152 48 155 85 Q 158 125 152 152 Q 145 168 100 168 Q 55 168 48 135 Q 42 100 48 70 Q 55 48 100 48", desc: "1. 圓框" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ע Ayin - Two legs curving to meet at bottom
    // ═══════════════════════════════════════════════════════════════════
    "ע": {
        strokes: [
            // Stroke 1: Right leg
            { path: "M 142 52 Q 130 50 125 65 L 125 138 Q 125 162 100 168", desc: "1. 右支" },
            // Stroke 2: Left leg
            { path: "M 62 52 Q 75 50 80 65 L 80 138 Q 80 162 100 168", desc: "2. 左支" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // פ Pe - Bowl frame with inner mouth element
    // ═══════════════════════════════════════════════════════════════════
    "פ": {
        strokes: [
            // Stroke 1: Outer bowl frame
            { path: "M 152 162 L 152 82 Q 152 52 115 48 L 88 48 Q 52 48 48 82 L 48 162", desc: "1. 外框" },
            // Stroke 2: Inner mouth/spiral
            { path: "M 138 78 Q 108 78 105 100 Q 104 120 118 128 Q 132 132 142 125", desc: "2. 內嘴" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ף Final Pe - Curved top with long descender
    // ═══════════════════════════════════════════════════════════════════
    "ף": {
        strokes: [
            // Stroke 1: Curved top flowing into descender
            { path: "M 148 52 Q 105 42 65 62 Q 48 78 45 100 L 45 190", desc: "1. 頂及長豎" },
            // Stroke 2: Inner mouth
            { path: "M 128 75 Q 95 75 92 98 Q 90 118 108 125 Q 122 128 132 120", desc: "2. 內嘴" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // צ Tsade - Right ascending element with left body
    // ═══════════════════════════════════════════════════════════════════
    "צ": {
        strokes: [
            // Stroke 1: Right ascending prong (goes above normal height)
            { path: "M 152 28 Q 150 45 150 70 L 150 162", desc: "1. 右上豎" },
            // Stroke 2: Left body curving to base
            { path: "M 88 58 Q 55 55 52 88 L 52 145 Q 52 162 82 162 L 150 162", desc: "2. 左體底" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ץ Final Tsade - Left body with descender
    // ═══════════════════════════════════════════════════════════════════
    "ץ": {
        strokes: [
            // Stroke 1: Left body and base
            { path: "M 88 58 Q 55 55 52 88 L 52 145 Q 52 162 82 162 L 135 162", desc: "1. 左體底" },
            // Stroke 2: Descender below baseline
            { path: "M 135 162 L 135 190", desc: "2. 下延" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ק Qof - Left cup with separate right descender
    // ═══════════════════════════════════════════════════════════════════
    "ק": {
        strokes: [
            // Stroke 1: Left cup/bowl
            { path: "M 108 162 L 108 82 Q 108 52 72 48 Q 42 48 38 80 L 38 162", desc: "1. 左杯" },
            // Stroke 2: Right descender (separate, goes below baseline)
            { path: "M 152 52 Q 142 50 140 68 L 140 190", desc: "2. 右下延" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ר Resh - Curved roof with right leg
    // ═══════════════════════════════════════════════════════════════════
    "ר": {
        strokes: [
            // Stroke 1: Curved roof
            { path: "M 152 52 Q 110 44 72 50 Q 52 56 42 68", desc: "1. 頂弧" },
            // Stroke 2: Right leg with slight curve
            { path: "M 148 52 Q 150 105 148 162", desc: "2. 右腿" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // שׁ Shin - Three prongs with curved tops, connected at base
    // Each prong has a distinctive curved head before going down
    // ═══════════════════════════════════════════════════════════════════
    "שׁ": {
        strokes: [
            // Stroke 1: Right prong - head curves right then down
            { path: "M 162 48 Q 155 42 150 48 Q 146 58 146 75 L 146 155", desc: "1. 右支" },
            // Stroke 2: Middle prong - tallest, small curved head
            { path: "M 112 42 Q 102 38 98 48 Q 96 60 96 78 L 98 155", desc: "2. 中支" },
            // Stroke 3: Left prong - head curves left then down
            { path: "M 48 52 Q 52 42 58 48 Q 62 58 60 75 L 58 155", desc: "3. 左支" },
            // Stroke 4: Base connecting all prongs
            { path: "M 146 155 Q 100 168 58 155", desc: "4. 底連" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // שׂ Sin - Same shape as Shin
    // ═══════════════════════════════════════════════════════════════════
    "שׂ": {
        strokes: [
            { path: "M 162 48 Q 155 42 150 48 Q 146 58 146 75 L 146 155", desc: "1. 右支" },
            { path: "M 112 42 Q 102 38 98 48 Q 96 60 96 78 L 98 155", desc: "2. 中支" },
            { path: "M 48 52 Q 52 42 58 48 Q 62 58 60 75 L 58 155", desc: "3. 左支" },
            { path: "M 146 155 Q 100 168 58 155", desc: "4. 底連" }
        ]
    },

    // ═══════════════════════════════════════════════════════════════════
    // ת Tav - Pi shape with left foot extending left
    // ═══════════════════════════════════════════════════════════════════
    "ת": {
        strokes: [
            // Stroke 1: Roof
            { path: "M 158 52 Q 105 44 55 52 Q 42 56 38 62", desc: "1. 頂橫" },
            // Stroke 2: Right leg
            { path: "M 152 52 L 152 162", desc: "2. 右腿" },
            // Stroke 3: Left leg with foot extending left
            { path: "M 62 58 L 62 162 L 32 162", desc: "3. 左腿腳" }
        ]
    }
};

/**
 * Get stroke data for a letter
 * @param {string} letter - Hebrew letter
 * @returns {object} Stroke data with paths array
 */
function getStrokePaths(letter) {
    // Remove vowel points for lookup
    const baseLetter = letter.replace(/[\u0591-\u05C7]/g, '');
    return strokePaths[baseLetter] || strokePaths[letter] || null;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { strokePaths, getStrokePaths };
}
