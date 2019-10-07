import pygame
from geometry import get_init_points
from constants import WIDTH, HEIGHT, MOVE_KEY_MAP, ROTATE_KEY_MAP, CW, ACW, MOVE, MOVE2LAYERS, ROTATE, OPPOSITE
from constants import SAVE_POSITION, RESET_POSITION, SAVE_KEY_MAP
from constants import F, B, L, R, U, D, COLORS
from copy import deepcopy
from geometry import z_orientation, xy_projection
from functools import reduce
from operator import add
from rubik import Rubik


def init_mouse_drag(points):
    dragging = False

    def handle_mouse_drag(event):
        nonlocal dragging
        if event.type == pygame.MOUSEBUTTONUP:
            dragging = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            dragging = True
            # Ignore initial relative value.
            pygame.mouse.get_rel()
        elif event.type == pygame.MOUSEMOTION and dragging:
            # Handle mouse drag HERE
            x, y = pygame.mouse.get_rel()
            for point in points:
                point.rotate_x_ip(y)
                point.rotate_y_ip(x)

    return handle_mouse_drag


def handle_save_points(points):
    saved_points = deepcopy(points)

    def save_positions():
        nonlocal saved_points
        saved_points = deepcopy(points)

    def reset_positions():
        for p, sp in zip(points, saved_points):
            p.update(sp)

    return save_positions, reset_positions


def init_handle_keys(init_move, save_positions, reset_positions):
    def handle_key_event(event):
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            direction = ACW if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT] else CW
            if event.key in MOVE_KEY_MAP:
                face = MOVE_KEY_MAP[event.key]
                if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                    init_move(direction, face, MOVE2LAYERS)
                else:
                    init_move(direction, face, MOVE)
            if event.key in ROTATE_KEY_MAP:
                face = ROTATE_KEY_MAP[event.key]
                init_move(direction, face, ROTATE)
            if event.key in SAVE_KEY_MAP:
                if SAVE_KEY_MAP[event.key] == SAVE_POSITION:
                    save_positions()
                elif SAVE_KEY_MAP[event.key] == RESET_POSITION:
                    reset_positions()

    return handle_key_event


def draw_surface(win, color, surf):
    if z_orientation(surf) > 0:
        pygame.draw.polygon(win, color, xy_projection(surf))
        pygame.draw.polygon(win, (128, 128, 128), xy_projection(surf), 1)


def surf_mid_point(surf):
    v = reduce(add, surf, pygame.Vector3()) / 4
    return v


def moving_points_on_move(face, centers, edges, corners):
    # The points that will be rotated when given face is rotated.
    points = []
    points.extend(centers[face])
    for edge in edges:
        if face in edge:
            for f in edge:
                points.extend(edges[edge][f])
    for corner in corners:
        if face in corner:
            for f in corner:
                points.extend(corners[corner][f])
    rotation_axis = surf_mid_point(centers[face])
    return points, rotation_axis


def moving_points_on_rotation(face, action, centers, edges, corners):
    # The points that will be rotated when given face is rotated.
    points = []
    if action == MOVE:
        points.extend(centers[face])
        for edge in edges:
            if face in edge:
                for f in edge:
                    points.extend(edges[edge][f])
        for corner in corners:
            if face in corner:
                for f in corner:
                    points.extend(corners[corner][f])
    elif action == MOVE2LAYERS:
        opp_face = OPPOSITE[face]
        for f in centers:
            if f != opp_face:
                points.extend(centers[f])
        for edge in edges:
            if opp_face not in edge:
                for f in edge:
                    points.extend(edges[edge][f])
        for corner in corners:
            if opp_face not in corner:
                for f in corner:
                    points.extend(corners[corner][f])
    elif action == ROTATE:
        for f in centers:
            points.extend(centers[f])
        for edge in edges:
            for f in edge:
                points.extend(edges[edge][f])
        for corner in corners:
            for f in corner:
                points.extend(corners[corner][f])

    rotation_axis = surf_mid_point(centers[face])
    return points, rotation_axis


def animation(rubik, centers, edges, corners):
    # Implements the animation for move.
    running = False
    step_angle = 5
    current_angle = 0
    rotation_points, rotation_axis = None, None
    rotation_face, rotation_direction = None, None
    rotation_action = None
    initial_points = None

    def in_progress():
        return running

    def init_move(direction, face, action):
        nonlocal rotation_points, rotation_axis, running, initial_points
        nonlocal rotation_face, rotation_direction, current_angle, rotation_action
        running = True
        rotation_action = action
        rotation_direction = direction
        rotation_face = face
        current_angle = 0
        rotation_points, rotation_axis = moving_points_on_rotation(face, action, centers, edges, corners)
        initial_points = deepcopy(rotation_points)

    def animate():
        nonlocal rotation_points, current_angle, running, initial_points
        for p in rotation_points:
            p.rotate_ip(-step_angle if rotation_direction == CW else step_angle, rotation_axis)
        current_angle = current_angle + step_angle
        if current_angle >= 90:
            for ip, rp in zip(initial_points, rotation_points):
                rp.update(ip)
            rubik.transform(rotation_direction, rotation_face, rotation_action)
            running = False

    return in_progress, init_move, animate


def draw_rubik(win, rubik, centers, edges, corners):
    surfaces = []
    for face in centers:
        surfaces.append((rubik.get_colors(face), centers[face]))
    for edge in edges:
        for face, color in zip(edge, rubik.get_colors(edge)):
            surfaces.append((color, edges[edge][face]))
    for corner in corners:
        # print(corner, rubik.get_colors(corner))
        for face, color in zip(corner, rubik.get_colors(corner)):
            surfaces.append((color, corners[corner][face]))

    # Sort the surfaces according to their average z axis
    # hinge that this will surfaces on top to be drawn later on.
    surfaces.sort(key=lambda v: surf_mid_point(v[1]).z)

    for color, surf in surfaces:
        draw_surface(win, color, surf)


def draw_orientation(win, rubik):
    w, h = WIDTH / 3.5, HEIGHT / 4
    f = lambda *v: tuple(int(i) for i in v)
    surf = pygame.Surface(f(w, h))
    surf.fill((128, 128, 128))
    rect = surf.get_rect()
    rect.bottomright = (WIDTH, HEIGHT)
    faces = {F: f(w / 5, h / 4, w / 5, h / 4), L: f(0, h / 4, w / 5, h / 4), U: f(w / 5, 0, w / 5, h / 4),
             D: f(w / 5, h / 2, w / 5, h / 4),
             R: f(2 * w / 5, h / 4, w / 5, h / 4), B: f(3 * w / 5, h / 4, w / 5, h / 4)}
    for f in faces:
        pygame.draw.rect(surf, rubik.get_colors(f), faces[f])
    win.blit(surf, rect)


def handle_rotation_keys(points):
    # Handle Key Inputs for Cube Rotation.
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        for p in points:
            p.rotate_x_ip(-1)
    if keys[pygame.K_DOWN]:
        for p in points:
            p.rotate_x_ip(1)
    if keys[pygame.K_LEFT]:
        for p in points:
            p.rotate_y_ip(-1)
    if keys[pygame.K_RIGHT]:
        for p in points:
            p.rotate_y_ip(1)
    if keys[pygame.K_LEFTBRACKET]:
        for p in points:
            p.rotate_z_ip(1)
    if keys[pygame.K_RIGHTBRACKET]:
        for p in points:
            p.rotate_z_ip(-1)


def mainloop():
    pygame.init()
    clock = pygame.time.Clock()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rubik's Cube")
    run = True
    rubik = Rubik()
    points, centers, edges, corners = get_init_points()
    save_positions, reset_positions = handle_save_points(points)
    handle_mouse_drag = init_mouse_drag(points)
    in_progress, init_move, animate = animation(rubik, centers, edges, corners)
    handle_key_event = init_handle_keys(init_move, save_positions, reset_positions)
    print(rubik)

    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                run = False
            if not in_progress():
                handle_key_event(event)
                handle_mouse_drag(event)
        if in_progress():
            animate()
        else:
            handle_rotation_keys(points)

        win.fill((128, 128, 128))
        draw_orientation(win, rubik)
        draw_rubik(win, rubik, centers, edges, corners)
        pygame.display.update()
    pygame.quit()


mainloop()
