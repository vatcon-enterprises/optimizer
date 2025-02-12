/*************************************************************************
*    CompuCell - A software framework for multimodel simulations of     *
* biocomplexity problems Copyright (C) 2003 University of Notre Dame,   *
*                             Indiana                                   *
*                                                                       *
* This program is free software; IF YOU AGREE TO CITE USE OF CompuCell  *
*  IN ALL RELATED RESEARCH PUBLICATIONS according to the terms of the   *
*  CompuCell GNU General Public License RIDER you can redistribute it   *
* and/or modify it under the terms of the GNU General Public License as *
*  published by the Free Software Foundation; either version 2 of the   *
*         License, or (at your option) any later version.               *
*                                                                       *
* This program is distributed in the hope that it will be useful, but   *
*      WITHOUT ANY WARRANTY; without even the implied warranty of       *
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU    *
*             General Public License for more details.                  *
*                                                                       *
*  You should have received a copy of the GNU General Public License    *
*     along with this program; if not, write to the Free Software       *
*      Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.        *
*************************************************************************/

#include <CompuCell3D/CC3D.h>
using namespace CompuCell3D;

using namespace std;

#include "ContactPlugin.h"


ContactPlugin::ContactPlugin() :xmlData(0), weightDistance(false) {
}

ContactPlugin::~ContactPlugin() {

}

void ContactPlugin::init(Simulator *simulator, CC3DXMLElement *_xmlData) {
    potts = simulator->getPotts();
    xmlData = _xmlData;
    simulator->getPotts()->registerEnergyFunctionWithName(this, toString());
    simulator->registerSteerableObject(this);
}

void ContactPlugin::extraInit(Simulator *simulator) {
    update(xmlData, true);
}

void ContactPlugin::update(CC3DXMLElement *_xmlData, bool _fullInitFlag) {
    automaton = potts->getAutomaton();

    if (!automaton) throw CC3DException("CELL TYPE PLUGIN WAS NOT PROPERLY INITIALIZED YET. MAKE SURE THIS IS THE FIRST PLUGIN THAT YOU SET");
    set<unsigned char> cellTypesSet;

    CC3DXMLElementList energyVec = _xmlData->getElements("Energy");

    contactEnergyArray.clear();

    for (int i = 0; i < energyVec.size(); ++i) {
        setContactEnergy(energyVec[i]->getAttribute("Type1"), energyVec[i]->getAttribute("Type2"), energyVec[i]->getDouble());
        //inserting all the types to the set (duplicate are automatically eleminated) to figure out max value of type Id
        cellTypesSet.insert(automaton->getTypeId(energyVec[i]->getAttribute("Type1")));
        cellTypesSet.insert(automaton->getTypeId(energyVec[i]->getAttribute("Type2")));
    }

    for (auto& i : cellTypesSet)
        for (auto& j : cellTypesSet)
            cerr << "contact[" << to_string(i) << "][" << to_string(j) << "]=" << contactEnergyArray[i][j] << endl;

    //Here I initialize max neighbor index for direct acces to the list of neighbors 
    boundaryStrategy = BoundaryStrategy::getInstance();
    maxNeighborIndex = 0;

    if (_xmlData->getFirstElement("WeightEnergyByDistance")) {
        weightDistance = true;
    }

    if (_xmlData->getFirstElement("Depth")) {
        maxNeighborIndex = boundaryStrategy->getMaxNeighborIndexFromDepth(_xmlData->getFirstElement("Depth")->getDouble());
        //cerr<<"got here will do depth"<<endl;
    }
    else {
        //cerr<<"got here will do neighbor order"<<endl;
        if (_xmlData->getFirstElement("NeighborOrder")) {

            maxNeighborIndex = boundaryStrategy->getMaxNeighborIndexFromNeighborOrder(_xmlData->getFirstElement("NeighborOrder")->getUInt());

        }
        else {
            maxNeighborIndex = boundaryStrategy->getMaxNeighborIndexFromNeighborOrder(1);

        }

    }

    cerr << "Contact maxNeighborIndex=" << maxNeighborIndex << endl;

}

double ContactPlugin::changeEnergy(const Point3D &pt, const CellG *newCell, const CellG *oldCell) {

    double energy = 0;
    unsigned int token = 0;
    double distance = 0;
    Point3D n;

    CellG *nCell = 0;
    WatchableField3D<CellG *> *fieldG = (WatchableField3D<CellG *> *) potts->getCellFieldG();
    Neighbor neighbor;

    if (weightDistance) {
        for (unsigned int nIdx = 0; nIdx <= maxNeighborIndex; ++nIdx) {
            neighbor = boundaryStrategy->getNeighborDirect(const_cast<Point3D&>(pt), nIdx);
            if (!neighbor.distance) {
                //if distance is 0 then the neighbor returned is invalid
                continue;
            }
            nCell = fieldG->get(neighbor.pt);
            if (nCell != oldCell) {
                if ((nCell != 0) && (oldCell != 0)) {
                    if ((nCell->clusterId) != (oldCell->clusterId)) {
                        energy -= contactEnergy(oldCell, nCell) / neighbor.distance;
                    }
                }
                else {
                    energy -= contactEnergy(oldCell, nCell) / neighbor.distance;
                }

            }
            if (nCell != newCell) {
                if ((newCell != 0) && (nCell != 0)) {
                    if ((newCell->clusterId) != (nCell->clusterId)) {
                        energy += contactEnergy(newCell, nCell) / neighbor.distance;
                    }
                }
                else {
                    energy += contactEnergy(newCell, nCell) / neighbor.distance;

                }
            }


        }
    }
    else {

        for (unsigned int nIdx = 0; nIdx <= maxNeighborIndex; ++nIdx) {
            neighbor = boundaryStrategy->getNeighborDirect(const_cast<Point3D&>(pt), nIdx);
            if (!neighbor.distance) {
                //if distance is 0 then the neighbor returned is invalid
                continue;
            }            
            nCell = fieldG->get(neighbor.pt);
            if (nCell != oldCell) {
                if ((nCell != 0) && (oldCell != 0)) {
                    if ((nCell->clusterId) != (oldCell->clusterId)) {
                        energy -= contactEnergy(oldCell, nCell);
                    }
                }
                else {
                    energy -= contactEnergy(oldCell, nCell);
                }

            }
            if (nCell != newCell) {

                if ((newCell != 0) && (nCell != 0)) {
                    if ((newCell->clusterId) != (nCell->clusterId)) {
                        energy += contactEnergy(newCell, nCell);
                    }
                }
                else {
                    energy += contactEnergy(newCell, nCell);

                }

            }


        }


    }

    return energy;
}

void ContactPlugin::setContactEnergy(const string typeName1, const string typeName2, const double energy) {

    unsigned char type1 = automaton->getTypeId(typeName1);
    unsigned char type2 = automaton->getTypeId(typeName2);

    contactEnergyArray[type1][type2] = energy;
    contactEnergyArray[type2][type1] = energy;
}

std::string ContactPlugin::steerableName() { return "Contact"; }
std::string ContactPlugin::toString() { return steerableName(); }
