from constants import ALL_MOVES
from constants import CENTERS, EDGES, CORNERS
from constants import F, B, L, R, U, D, CW, ACW
from constants import NEIGHBORS, OPPOSITE
from random import choice


class RubikUtilities:
    @staticmethod
    def shuffle(rubik, steps):
        for _ in range(steps):
            direction, face = RubikUtilities.random_move()
            rubik.move(direction, face)

    @staticmethod
    def random_move():
        return choice(ALL_MOVES)

    @staticmethod
    def is_solved(rubik):
        color_map = {f: rubik.get_colors(f) for f in CENTERS}
        print(color_map)
        for corner in CORNERS:
            if tuple(color_map[f] for f in corner) == rubik.get_colors(corner):
                continue
            print('OUT OF PLACE CORNER:', corner, 'COLOR MAP:', color_map)
            return False
        for edge in EDGES:
            if tuple(color_map[f] for f in edge) == rubik.get_colors(edge):
                continue
            print('OUT OF PLACE EDGE:', edge, 'COLOR MAP:', color_map)
            return False
        return True


ORDER = [R, L, U, D, F, B]
o = lambda *f: tuple(sorted(f, key=lambda i: ORDER.index(i)))


class RubikSolver:
    @staticmethod
    def make_bottom_cross(rubik, base=D):
        # Makes a cross at the bottom (down face).
        b_c = rubik.get_center(position=base)
        nbr_c = [rubik.get_center(position=f) for f in NEIGHBORS[base]]
        cross_edges = [rubik.get_edge(colors=(b_c.color, c.color)) for c in nbr_c]
        for index, edge in enumerate(cross_edges):
            # TODO: Dont do these steps if already in place.
            # Bring the cross edges to top
            if base in edge.positions:
                face = edge.positions[0 if edge.positions[1] == base else 1]
                rubik.move(CW, face, 2)

            if OPPOSITE[base] not in edge.positions:
                top_rotated = False
                face = edge.positions[0]
                for _ in range(4):
                    rubik.move(CW, face)
                    if OPPOSITE[base] in edge.positions and not top_rotated:
                        rubik.move(CW, OPPOSITE[base])
                        top_rotated = True

            # Move it over right place
            while nbr_c[index].position not in edge.positions:
                rubik.move(CW, OPPOSITE[base])

            # Now right above two cases.
            if (nbr_c[index].color == edge.colors[0] and nbr_c[index].position == edge.positions[0]) or \
                    (nbr_c[index].color == edge.colors[1] and nbr_c[index].position == edge.positions[1]):
                # If right orientation
                rubik.move(CW, nbr_c[index].position, 2)
            else:
                rubik.move(CW, OPPOSITE[base])
                face = edge.positions[0 if edge.positions[1] == OPPOSITE[base] else 1]
                rubik.move(CW, face)
                rubik.move(ACW, nbr_c[index].position)
                rubik.move(ACW, face)

        for index, edge in enumerate(cross_edges):
            for position, color in zip(edge.positions, edge.colors):
                assert rubik.get_center(position=position).color == color

    @staticmethod
    def make_bottom_corners(rubik, base=D):
        b_c = rubik.get_center(position=base)
        nbr_c = [rubik.get_center(position=f) for f in NEIGHBORS[base]]
        corners = [rubik.get_corner(colors=tuple(rubik.get_colors(f) for f in c)) for c in CORNERS if base in c]
        for corner in corners:
            # First move the corner to top later.
            if base in corner.positions:
                top_rotated = False
                return_direction = None
                face = corner.positions[0 if corner.positions[1] == base else 1]  # Any face would do
                for index in range(4):
                    rubik.move(CW, face)
                    if OPPOSITE[base] in corner.positions and not top_rotated:
                        if index == 0:
                            rubik.move(CW, OPPOSITE[base])
                            return_direction = ACW
                            top_rotated = True
                        if index == 2:
                            rubik.move(ACW, OPPOSITE[base])
                            return_direction = CW
                            top_rotated = True
                rubik.move(return_direction, OPPOSITE[base])
            # Move it to the right place on top
            while set(corner.colors) != set(
                    rubik.get_colors(p if p != OPPOSITE[base] else base) for p in corner.positions):
                rubik.move(CW, OPPOSITE[base])
            # Now put it in place.
            face = None
            while corner.colors != tuple(rubik.get_colors(p) for p in corner.positions):
                positions = corner.positions
                rubik.move(CW, OPPOSITE[base])
                if face is None:
                    face = next(p for p in positions if p not in corner.positions)
                rubik.move(CW, face)
                rubik.move(ACW, OPPOSITE[base])
                rubik.move(ACW, face)
        for corner in corners:
            assert corner.colors == tuple(rubik.get_colors(p) for p in corner.positions)

    @staticmethod
    def solve_middle_layer(rubik, base=D):
        # Algorithm definitions
        def left_algorithm(left, up, front):
            # Algorithm: U' L' U L U F U' F'
            rubik.move(ACW, up)
            rubik.move(ACW, left)
            rubik.move(CW, up)
            rubik.move(CW, left)
            rubik.move(CW, up)
            rubik.move(CW, front)
            rubik.move(ACW, up)
            rubik.move(ACW, front)

        def right_algorithm(right, up, front):
            # Algorithm: U R U' R' U' F' U F
            rubik.move(CW, up)
            rubik.move(CW, right)
            rubik.move(ACW, up)
            rubik.move(ACW, right)
            rubik.move(ACW, up)
            rubik.move(ACW, front)
            rubik.move(CW, up)
            rubik.move(CW, front)

        up_side = OPPOSITE[base]
        # The edges which need to be placed in order, without impacting the lower layers
        edges = []
        for e in EDGES:
            edge = rubik.get_edge(positions=e)
            if rubik.get_center(position=base).color not in edge.colors and \
                    rubik.get_center(position=up_side).color not in edge.colors:
                edges.append(edge)

        for index, edge in enumerate(edges):
            # Make sure that the edge is on top.
            # If not push any other available edge to occupy its place
            if up_side not in edge.positions:
                print('GETTING OUT AN EDGE.')
                # any side of the edge
                some_face = edge.positions[0]
                other_face = edge.positions[1]
                rubik.move(CW, some_face)
                if up_side in edge.positions:
                    rubik.move(ACW, some_face)
                    left_algorithm(other_face, up_side, some_face)
                else:
                    rubik.move(ACW, some_face)
                    right_algorithm(other_face, up_side, some_face)

            assert up_side in edge.positions

            front_color = edge.colors[0 if edge.positions[1] == up_side else 1]
            up_color = edge.colors[0 if edge.positions[0] == up_side else 1]
            front_side = rubik.get_center(color=front_color).position
            # Now move the edge around the top such that center and edge have a common color
            # so as to apply the algorithms later on.
            while front_side not in edge.positions:
                rubik.move(CW, up_side)

            # Now figure out which direction to apply the algorithm
            # simply move top side to determine the orientations to apply algorithm.
            # if after moving to top clockwise, determine if edge has a common color with the center.
            # and take action accordingly.
            rubik.move(CW, up_side)
            if rubik.get_center(color=up_color).position in edge.positions:
                rubik.move(ACW, up_side)
                left_side = rubik.get_center(color=up_color).position
                left_algorithm(left_side, up_side, front_side)
            else:
                rubik.move(ACW, up_side)
                right_side = rubik.get_center(color=up_color).position
                right_algorithm(right_side, up_side, front_side)

        for edge in edges:
            assert edge.colors == tuple(rubik.get_colors(f) for f in edge.positions)

    @staticmethod
    def solve_top_cross(rubik, base=D):
        def algorithm(right, up, front):
            # Algorithm: F R U R' U' F'
            rubik.move(CW, front)
            rubik.move(CW, right)
            rubik.move(CW, up)
            rubik.move(ACW, right)
            rubik.move(ACW, up)
            rubik.move(ACW, front)

        up_side = OPPOSITE[base]
        up_color = rubik.get_colors(up_side)
        edges = list(filter(lambda _edge: up_side in _edge.positions, [rubik.get_edge(positions=e) for e in EDGES]))

        top_facing_edges = lambda: list(
            filter(lambda _edge: _edge.colors[_edge.positions.index(up_side)] == up_color, edges))

        if len(top_facing_edges()) == 0:
            # now orientation is required to apply the algorithm
            some_edge = edges[0]
            right_side = some_edge.positions[0 if some_edge.positions[1] == up_side else 1]
            rubik.move(CW, up_side)
            front_side = some_edge.positions[0 if some_edge.positions[1] == up_side else 1]
            rubik.move(ACW, up_side)

            # Apply the algorithm to obtain at least 2 edges
            algorithm(right_side, up_side, front_side)

        assert len(top_facing_edges()) > 0
        if len(top_facing_edges()) == 2:
            facing_edges = top_facing_edges()
            edge1_side = facing_edges[0].positions[0 if facing_edges[0].positions[1] == up_side else 1]
            edge2_side = facing_edges[1].positions[0 if facing_edges[1].positions[1] == up_side else 1]

            if OPPOSITE[edge1_side] != edge2_side:
                # L shape
                # Apply algorithm to convert it to line orientation.
                # First determine Orientation to apply algorithm
                rubik.move(CW, up_side)
                if edge2_side == facing_edges[0].positions[0 if facing_edges[0].positions[1] == up_side else 1]:
                    # If moving CW, edge1 moves to edge2. Then opposite of initial edge2 is front side.
                    rubik.move(ACW, up_side)
                    front_side, right_side = OPPOSITE[edge2_side], OPPOSITE[edge1_side]
                    algorithm(right_side, up_side, front_side)
                else:
                    rubik.move(ACW, up_side)
                    front_side, right_side = OPPOSITE[edge1_side], OPPOSITE[edge2_side]
                    algorithm(right_side, up_side, front_side)

            facing_edges = top_facing_edges()
            edge1_side = facing_edges[0].positions[0 if facing_edges[0].positions[1] == up_side else 1]
            edge2_side = facing_edges[1].positions[0 if facing_edges[1].positions[1] == up_side else 1]
            assert OPPOSITE[edge1_side] == edge2_side
            # Now there must be I shape

            rubik.move(CW, up_side)
            right_side = edge1_side
            front_side = facing_edges[0].positions[0 if facing_edges[0].positions[1] == up_side else 1]
            rubik.move(ACW, up_side)
            algorithm(right_side, up_side, front_side)

        # By the end of this step, top must contain a cross.
        assert len(top_facing_edges()) == 4

    @staticmethod
    def solve_top_edges(rubik, base=D):
        def algorithm(right, up):
            # Algorithm: R U R' U R U2 R' U
            rubik.move(CW, right)
            rubik.move(CW, up)
            rubik.move(ACW, right)
            rubik.move(CW, up)
            rubik.move(CW, right)
            rubik.move(CW, up, 2)
            rubik.move(ACW, right)
            rubik.move(CW, up)

        up_side = OPPOSITE[base]
        up_color = rubik.get_colors(up_side)
        edges = list(filter(lambda _edge: up_side in _edge.positions, [rubik.get_edge(positions=e) for e in EDGES]))

        def aligned_top_edges():
            return list(filter(lambda _edge: rubik.get_colors(
                _edge.positions[0 if _edge.positions[1] == up_side else 1]) in _edge.colors, edges))

        while len(aligned_top_edges()) <= 1:
            rubik.move(CW, up_side)

        aligned_edges = aligned_top_edges()
        if len(aligned_edges) == 4:
            # No need for any algorithm already aligned
            return

        assert len(aligned_edges) == 2

        edge1_side = aligned_edges[0].positions[0 if aligned_edges[0].positions[1] == up_side else 1]
        edge2_side = aligned_edges[1].positions[0 if aligned_edges[1].positions[1] == up_side else 1]
        if OPPOSITE[edge1_side] == edge2_side:
            # Aligned edges in opposite to each other.
            # apply algorithm to convert it into L pattern
            # any side would do for algorithm orientation not required
            print('Converting OPPOSITES TO L')
            algorithm(edge1_side, up_side)

        # Update the aligned top edges in case conversion took place.
        while len(aligned_top_edges()) <= 1:
            rubik.move(CW, up_side)

        aligned_edges = aligned_top_edges()
        edge1_side = aligned_edges[0].positions[0 if aligned_edges[0].positions[1] == up_side else 1]
        edge2_side = aligned_edges[1].positions[0 if aligned_edges[1].positions[1] == up_side else 1]
        assert OPPOSITE[edge1_side] != edge2_side

        # Not oriented top edge orientation must have L shape
        # Orientation is now required for the algorithm to complete this step.
        rubik.move(CW, up_side)
        right_side = edge1_side
        if edge2_side == aligned_edges[0].positions[0 if aligned_edges[0].positions[1] == up_side else 1]:
            right_side = edge2_side
        rubik.move(ACW, up_side)
        algorithm(right_side, up_side)

        assert len(aligned_top_edges()) == 4

    @staticmethod
    def solve_position_top_corners(rubik, base=D):
        def algorithm(left, right, up):
            # Algorithm: U R U' L' U R' U' L
            rubik.move(CW, up)
            rubik.move(CW, right)
            rubik.move(ACW, up)
            rubik.move(ACW, left)
            rubik.move(CW, up)
            rubik.move(ACW, right)
            rubik.move(ACW, up)
            rubik.move(CW, left)

        up_side = OPPOSITE[base]
        up_color = rubik.get_colors(up_side)
        corners = list(filter(lambda cnr: up_color in cnr.colors, [rubik.get_corner(positions=c) for c in CORNERS]))

        def aligned_top_corners():
            return list(filter(lambda cnr: set(cnr.colors) == set(rubik.get_colors(f) for f in cnr.positions), corners))

        # print(aligned_top_corners())
        if len(aligned_top_corners()) == 0:
            # Simply apply the algorithm.
            # Then one of them will auto align
            left_side = NEIGHBORS[up_side][0]
            right_side = OPPOSITE[left_side]
            algorithm(left_side, right_side, up_side)

        while len(aligned_top_corners()) == 1:
            # print(' WHILE LOOP:', aligned_top_corners())
            aligned_corner = aligned_top_corners()[0]
            side1, side2 = list(filter(lambda f: f != up_side, aligned_corner.positions))
            rubik.move(CW, up_side)
            right_side = side2 if side1 in aligned_corner.positions else side1
            left_side = OPPOSITE[right_side]
            rubik.move(ACW, up_side)

            algorithm(left_side, right_side, up_side)

        # print(aligned_top_corners())
        assert len(aligned_top_corners()) == 4

    @staticmethod
    def solve_orient_top_corners(rubik, base=D):
        def algorithm(right, down):
            # Algorithm: R' D' R D
            rubik.move(ACW, right)
            rubik.move(ACW, down)
            rubik.move(CW, right)
            rubik.move(CW, down)

        up_side = OPPOSITE[base]
        up_color = rubik.get_colors(up_side)
        corners = list(filter(lambda cnr: up_color in cnr.colors, [rubik.get_corner(positions=c) for c in CORNERS]))
        non_oriented_top_corners = lambda: list(
            filter(lambda cnr: cnr.colors != tuple(rubik.get_colors(f) for f in cnr.positions), corners))
        if not non_oriented_top_corners():
            # If all are already oriented
            return
        chosen_position = non_oriented_top_corners()[-1].positions

        # Now identify the right side.
        side1, side2 = list(filter(lambda f: f != up_side, chosen_position))
        rubik.move(CW, up_side)
        right_side = side1 if side1 in chosen_position else side2
        rubik.move(ACW, up_side)
        print('RIGHT SIDE:', right_side, chosen_position, up_side, base)
        print('NONE ORIENTED TOP CORNERS:', non_oriented_top_corners())
        non_oriented_corners = non_oriented_top_corners()
        for index, corner in enumerate(non_oriented_corners):
            # Rotate till corner in chosen location
            print(index, 'CORNER:', corner)
            count = 0
            while corner.positions != chosen_position:
                count += 1
                print(index, 'ROTATING TOP:', corner.positions, chosen_position)
                rubik.move(CW, up_side)

            while up_side not in corner.positions or corner.colors[corner.positions.index(up_side)] != up_color:
                print('CORNER:', count, index, corner, chosen_position, right_side, base, non_oriented_corners)
                algorithm(right_side, base)

        # Now only top layer must be mis-aligned.
        assert not non_oriented_top_corners()

    @staticmethod
    def solve_top_layer(rubik, base=D):
        RubikSolver.solve_top_cross(rubik, base)
        RubikSolver.solve_top_edges(rubik, base)
        RubikSolver.solve_position_top_corners(rubik, base)
        RubikSolver.solve_orient_top_corners(rubik, base)

    @staticmethod
    def solve(rubik, base=D):
        RubikSolver.make_bottom_cross(rubik, base)
        RubikSolver.make_bottom_corners(rubik, base)
        RubikSolver.solve_middle_layer(rubik, base)
        RubikSolver.solve_top_layer(rubik, base)
