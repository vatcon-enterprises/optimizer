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

#ifndef CONTACTMULTICADPLUGIN_H
#define CONTACTMULTICADPLUGIN_H


#include <CompuCell3D/CC3D.h>

#include "ContactMultiCadData.h"

#include "ContactMultiCadDLLSpecifier.h"


class CC3DXMLElement;

namespace CompuCell3D {
  class Simulator;

  class Potts3D;
  class Automaton;
  class ContactMultiCadData;
  class BoundaryStrategy;


  class CONTACTMULTICAD_EXPORT ContactMultiCadPlugin : public Plugin,public EnergyFunction {
  public:
    typedef double (ContactMultiCadPlugin::*contactEnergyPtr_t)(const CellG *cell1, const CellG *cell2);


   private:
    ExtraMembersGroupAccessor<ContactMultiCadData> contactMultiCadDataAccessor;
	CC3DXMLElement *xmlData;
    Potts3D *potts;
    Simulator *sim;
	//Energy function data

    typedef std::unordered_map<unsigned char, std::unordered_map<unsigned char, double> > contactEnergyArray_t;
    typedef std::vector<std::vector<double> > cadherinSpecificityArray_t;
    
    std::set<std::string> cadherinNameSet;
    std::vector<std::string> cadherinNameOrderedVector;


    contactEnergyArray_t contactEnergyArray;

    cadherinSpecificityArray_t cadherinSpecificityArray;
    std::map<std::string,unsigned int> mapCadNameToIndex;
    unsigned int numberOfCadherins;
        
    std::string contactFunctionType;
    std::string autoName;
    double depth;
    
    std::list<CadherinData> cadherinDataList;

    ExtraMembersGroupAccessor<ContactMultiCadData> * contactMultiCadDataAccessorPtr;

    Automaton *automaton;
    bool weightDistance;
    
    contactEnergyPtr_t contactEnergyPtr;

    unsigned int maxNeighborIndex;
    BoundaryStrategy *boundaryStrategy;
    float energyOffset;




  public:

    ContactMultiCadPlugin();
    virtual ~ContactMultiCadPlugin();

    ExtraMembersGroupAccessor<ContactMultiCadData> * getContactMultiCadDataAccessorPtr(){return & contactMultiCadDataAccessor;}


	virtual double changeEnergy(const Point3D &pt, const CellG *newCell, const CellG *oldCell);

	virtual void init(Simulator *simulator, CC3DXMLElement *_xmlData);
		

	virtual void extraInit(Simulator *simulator);
    



    //Steerrable interface
    virtual void update(CC3DXMLElement *_xmlData, bool _fullInitFlag=false);
    virtual std::string steerableName();
    virtual std::string toString();

	//Energy Function fcns
  	double contactEnergy(const CellG *cell1, const CellG *cell2);
	    /**
     * @return The contact energy between cell1 and cell2.
     */
    double contactEnergyLinear(const CellG *cell1, const CellG *cell2);
    void setContactEnergy(const std::string typeName1,
	const std::string typeName2, const double energy);


  };
};
#endif
