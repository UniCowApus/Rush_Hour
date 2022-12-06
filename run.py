
from bauhaus import Encoding, proposition, constraint
from boardconfig import boardconfig

# Encoding that will store all of your constraints
E = Encoding()

#Example initial board configs:
solvableComplexExample = boardconfig([ 
    [0,0,6,2,2,2],
    [0,0,6,0,0,5],
    [4,4,0,1,1,5], # <-EXIT
    [0,3,0,0,0,0],
    [0,3,0,0,0,0],
    [0,3,0,0,0,0]
    ],
    [0,1,2,3,4,5,6],
    {0: "EMPTY", 1: "HORIZONTAL", 2: "HORIZONTAL", 3: "VERTICAL", 4: "HORIZONTAL", 5: "VERTICAL", 6: "VERTICAL"},
    4)

solveableSimpleExample = boardconfig([ 
    [0,0,0,0,0,0],
    [0,0,0,0,0,2],
    [0,0,0,1,1,2], # <-EXIT
    [0,0,0,0,0,0],
    [0,0,0,0,0,0],
    [0,0,0,0,0,0]
    ],
    [0,1,2],
    {0: "EMPTY", 1: "HORIZONTAL", 2: "VERTICAL"},
    2)

unsolveableExample = boardconfig([ 
    [0,0,0,0,0,2],
    [0,0,0,0,0,2],
    [0,0,0,1,1,2], # <-EXIT
    [0,0,0,0,0,3],
    [0,0,0,0,0,3],
    [0,0,0,0,0,3]
    ],
    [0,1,2],
    {0: "EMPTY", 1: "HORIZONTAL", 2: "VERTICAL", 3: "VERTICAL"},
    1)

activeConfig = solveableSimpleExample ## Change this to set which example model to run (I don't recomend complex unless you have a couple hours to burn);

#Configurable parameters
BOARD_ARRAY = activeConfig.boardArray
CAR_IDS = activeConfig.carIds
CAR_ORIENTATIONS = activeConfig.carOrientations
TOTAL_MOVES = activeConfig.totalMoves


#Set parameters
X_POSITIONS = [0,1,2,3,4,5]
Y_POSITIONS = [0,1,2,3,4,5]
MOVEMENTS = ["LEFT", "RIGHT", "UP", "DOWN", "HOLD"]
ORIENTATIONS = ["VERTICAl", "HORIZONTAL", "EMPTY"]
TIME = range(0,TOTAL_MOVES+1,1)



class Unique(object):
    def __hash__(self):
        return hash(str(self))
    def __eq__(self, other):
        return hash(self) == hash(other)
    def __repr__(self):
        return str(self)
    def __str__(self):
        assert False, "You need to define the __str__ function on a proposition class"



# To create propositions, create classes for them first, annotated with "@proposition" and the Encoding
@proposition(E)
class TileState(Unique):
    def __init__(self, carId, xPos, yPos, time):
        self.carId = carId
        self.xPos = xPos
        self.yPos = yPos
        self.time = time

    def __str__(self):
        return f"tileState(x{self.xPos}:y{self.yPos}:t{self.time})={self.carId}"


@proposition(E)
class CarMoves(Unique):
    def __init__(self, carId, direction, time):
        self.carId = carId
        self.direction = direction
        self.time = time
    def __str__(self):
        return f"CarMoves(car{self.carId}:d{self.direction}:t{self.time})"
        
@proposition(E)
class WinState(Unique):
    def __init__(self,time):
        self.time = time
    def __str__(self):
        return f"WinState({self.time})"

@proposition(E)
class ToBeSwapped(Unique): #override to prevent empty tiles from holding position when being moved into
    def __init__(self, xPos, yPos, time):
        self.xPos = xPos
        self.yPos = yPos
        self.time = time
    def __str__(self):
        return f"ToBeSwapped(x{self.xPos}:y{self.yPos}:t{self.time})"

        

##Constraints:

#The game is won when the red car is at the exit
#could be optimized for when all empty spaces in front of car
for t in TIME: 
    for car in CAR_IDS:
        if not car == 1:
            E.add_constraint((TileState(car,5,2,t)) >> ~WinState(t)) #don't just conclude winstate whenever it wants.
#A tile can only have one car at a time
for t in TIME:
    for x in X_POSITIONS:
        for y in Y_POSITIONS:
            for c in CAR_IDS:
                for other_car in CAR_IDS:
                    if not c == other_car:
                        E.add_constraint(TileState(c,x,y,t) >> ~TileState(other_car,x,y,t))

#car pieces move together
for t in TIME[:-1]:
    for x in X_POSITIONS:
        for y in Y_POSITIONS:
            for car in CAR_IDS:
                E.add_constraint((CarMoves(car,"UP",t) & TileState(car,x,y,t)) >> TileState(car,x,y-1,t+1))
                E.add_constraint((CarMoves(car,"DOWN",t) & TileState(car,x,y,t)) >> TileState(car,x,y+1,t+1))
                E.add_constraint((CarMoves(car,"LEFT",t) & TileState(car,x,y,t)) >> TileState(car,x-1,y,t+1))
                E.add_constraint((CarMoves(car,"RIGHT",t) & TileState(car,x,y,t)) >> TileState(car,x+1,y,t+1))
                E.add_constraint((CarMoves(car,"HOLD",t) & TileState(car,x,y,t) & ~ToBeSwapped(x,y,t)) >> TileState(car,x,y,t+1))

#a car can only move in the axis that it is oriented in.
for t in TIME:
    for car in CAR_IDS:
        if CAR_ORIENTATIONS[car] == "VERTICAL":
            E.add_constraint(~CarMoves(car,"LEFT",t) & ~CarMoves(car,"RIGHT",t))
        if CAR_ORIENTATIONS[car] == "HORIZONTAL":
            E.add_constraint(~CarMoves(car,"UP",t) & ~CarMoves(car,"DOWN",t))
        if CAR_ORIENTATIONS[car] == "EMPTY":
            E.add_constraint(CarMoves(car,"HOLD",t))

#a car must stay in bounds
for t in TIME:
    for car in CAR_IDS:
        for x in X_POSITIONS:
            E.add_constraint(TileState(car,x,0,t) >> ~CarMoves(car,"UP",t)) #don't move up if in top row
            E.add_constraint(TileState(car,x,5,t) >> ~CarMoves(car,"DOWN",t)) #don't move down if in bottom row
        for y in Y_POSITIONS:
            E.add_constraint(TileState(car,0,y,t) >> ~CarMoves(car,"LEFT",t)) #don't move left if in left column
            E.add_constraint(TileState(car,5,y,t) >> ~CarMoves(car,"RIGHT",t)) #don't move right if in right column
                

#only one move per time
for t in TIME[:-1]:
    constraint.add_exactly_one(E,[CarMoves(car,movement,t) for car in CAR_IDS[1:] for movement in MOVEMENTS[:-1]]) #We don't want to move empty spaces, so exlude first index from CAR_IDS. Also don't want cars to hold, so dont include that
        

#a car can only move in one direction at once
for t in TIME:
    for car in CAR_IDS:
        for d in MOVEMENTS:
            for dOther in MOVEMENTS:
                if not d == dOther:
                    E.add_constraint(CarMoves(car,d,t) >> ~CarMoves(car,dOther,t))


#one car moving implies other cars will hold
for t in TIME:
    for d in MOVEMENTS[:-1]: #if a car is holding, then it doesn't mean other cars must hold, so don't include hold movement
        for activeCar in CAR_IDS:
            for otherCar in CAR_IDS:
                if not activeCar == otherCar:
                    E.add_constraint(CarMoves(activeCar,d,t) >> CarMoves(otherCar,"HOLD",t))
        

#An empty tile will switch into one of the previous positions of a car when it is moved into. An empty tile will also be filled, so don't hold that position.
for t in TIME:
    for x in X_POSITIONS:
        for y in Y_POSITIONS:
            for d in MOVEMENTS:
                for car in CAR_IDS:
                    E.add_constraint((CarMoves(car,"UP",t) & TileState(car,x,y,t) & ~TileState(car,x,y-1,t)) >> (ToBeSwapped(x,y-1,t))) #if this is front of the car, don't hold the tile it's going to move into
                    E.add_constraint((CarMoves(car,"DOWN",t) & TileState(car,x,y,t) & ~TileState(car,x,y+1,t)) >> (ToBeSwapped(x,y+1,t))) 
                    E.add_constraint((CarMoves(car,"LEFT",t) & TileState(car,x,y,t) & ~TileState(car,x-1,y,t)) >> (ToBeSwapped(x-1,y,t))) 
                    E.add_constraint((CarMoves(car,"RIGHT",t) & TileState(car,x,y,t) & ~TileState(car,x+1,y,t)) >> (ToBeSwapped(x+1,y,t)))

                    E.add_constraint((CarMoves(car,"RIGHT",t) & TileState(car,x,y,t) & ~TileState(car,x-1,y,t)) >> (TileState(0,x,y,t+1))) #if this is the back of the car, then it will be filled with a empty tile
                    E.add_constraint((CarMoves(car,"LEFT",t) & TileState(car,x,y,t) & ~TileState(car,x+1,y,t)) >> (TileState(0,x,y,t+1)))
                    E.add_constraint((CarMoves(car,"DOWN",t) & TileState(car,x,y,t) & ~TileState(car,x,y-1,t)) >> (TileState(0,x,y,t+1)))
                    E.add_constraint((CarMoves(car,"UP",t) & TileState(car,x,y,t) & ~TileState(car,x,y+1,t)) >> (TileState(0,x,y,t+1)))


#if one tile is to be swapped, then all other tiles are not to be swapped
for t in TIME:
    for x in X_POSITIONS:
        for y in Y_POSITIONS:
            for otherX in X_POSITIONS:
                for otherY in Y_POSITIONS:
                    if not (x == otherX and y == otherY): 
                        E.add_constraint(ToBeSwapped(x,y,t) >> ~ToBeSwapped(otherX,otherY,t))
#only empty tiles can be swapped
for t in TIME:
    for x in X_POSITIONS:
        for y in Y_POSITIONS:
            for car in CAR_IDS[1:]:
                E.add_constraint(TileState(car,x,y,t) >> ~ToBeSwapped(x,y,t))

def test_theory():

    #Add constraints specified by board string
    for y in Y_POSITIONS: 
        for x in X_POSITIONS:
            E.add_constraint(TileState(BOARD_ARRAY[y][x],x,y,0));

    #Add winstate at specified time
    E.add_constraint(WinState(TOTAL_MOVES))
    return E

def visualize(solution):
    visual = {}
    for t in TIME:
        visual[t] = [[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]]
    for prep in solution.keys():
        if solution[prep] == True:
            prepStr = str(prep)
            if "tileState" in prepStr:
                if int(prepStr[17]) in TIME and (not (int(prepStr[11]) > 5 or int(prepStr[14]) > 5)):
                    visual[int(prepStr[17])][int(prepStr[14])][int(prepStr[11])]=int(prepStr[20])
    return visual
    

if __name__ == "__main__":

    T = test_theory()
    T = T.compile()
    print("\nSatisfiable: %s" % T.satisfiable())
    if(T.satisfiable):
        solution = T.solve()
    
        for prep in solution.keys():
            if solution[prep] == True:
                print(prep)
    
        visual = visualize(solution)
        for boardState in visual.keys():
            print("Move: "+ str(boardState))
            for line in visual[boardState]:
                print(line)

