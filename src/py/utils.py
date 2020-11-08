import vtk
import LinearSubdivisionFilter as lsf
import numpy as np
import math 
import os
import sys
import itk
from readers import OFFReader

def Normalization(vtkdata):
	polypoints = vtkdata.GetPoints()
	
	nppoints = []
	for pid in range(polypoints.GetNumberOfPoints()):
		spoint = polypoints.GetPoint(pid)
		nppoints.append(spoint)

	npmean = np.mean(np.array(nppoints), axis=0)
	nppoints -= npmean
	npscale = np.max([np.linalg.norm(p) for p in nppoints])
	nppoints /= npscale

	for pid in range(polypoints.GetNumberOfPoints()):
		vtkdata.GetPoints().SetPoint(pid, nppoints[pid])

	return vtkdata, npmean, npscale

def normalize_points(poly, radius):
	polypoints = poly.GetPoints()
	for pid in range(polypoints.GetNumberOfPoints()):
		spoint = polypoints.GetPoint(pid)
		spoint = np.array(spoint)
		norm = np.linalg.norm(spoint)
		spoint = spoint/norm * radius
		polypoints.SetPoint(pid, spoint)
	poly.SetPoints(polypoints)
	return poly

def normalize_vector(x):
	return x/np.linalg.norm(x)

def CreateIcosahedron(radius, sl):
	icosahedronsource = vtk.vtkPlatonicSolidSource()
	icosahedronsource.SetSolidTypeToIcosahedron()
	icosahedronsource.Update()
	icosahedron = icosahedronsource.GetOutput()
	
	subdivfilter = lsf.LinearSubdivisionFilter()
	subdivfilter.SetInputData(icosahedron)
	subdivfilter.SetNumberOfSubdivisions(sl)
	subdivfilter.Update()

	icosahedron = subdivfilter.GetOutput()
	icosahedron = normalize_points(icosahedron, radius)

	return icosahedron

def CreateSpiral(sphereRadius=4, numberOfSpiralSamples=64, numberOfSpiralTurns=4):
	
    sphere = vtk.vtkPolyData()
    sphere_points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    vertices = vtk.vtkCellArray()

    c = 2.0*float(numberOfSpiralTurns)
    prevPid = -1

    for i in range(numberOfSpiralSamples):
      p = [0, 0, 0]
      #angle = i * 180.0/numberOfSpiralSamples * math.pi/180.0
      angle = (i*math.pi)/numberOfSpiralSamples
      p[0] = sphereRadius * math.sin(angle)*math.cos(c*angle)
      p[1] = sphereRadius * math.sin(angle)*math.sin(c*angle)
      p[2] = sphereRadius * math.cos(angle)

      pid = sphere_points.InsertNextPoint(p)
      
      if(prevPid != -1):
        line = vtk.vtkLine()
        line.GetPointIds().SetId(0, prevPid)
        line.GetPointIds().SetId(1, pid)
        lines.InsertNextCell(line)

      prevPid = pid

      vertex = vtk.vtkVertex()
      vertex.GetPointIds().SetId(0, pid)

      vertices.InsertNextCell(vertex)
    
    sphere.SetVerts(vertices)
    sphere.SetLines(lines)
    sphere.SetPoints(sphere_points)

    return sphere

def CreatePlane(Origin,Point1,Point2,Resolution):
	plane = vtk.vtkPlaneSource()
	
	plane.SetOrigin(Origin)
	plane.SetPoint1(Point1)
	plane.SetPoint2(Point2)
	plane.SetXResolution(Resolution)
	plane.SetYResolution(Resolution)
	plane.Update()
	return plane.GetOutput()

def ReadSurf(fileName):

	print("Reading:", fileName)

	fname, extension = os.path.splitext(fileName)
	extension = extension.lower()
	if extension == ".vtk":
		reader = vtk.vtkPolyDataReader()
		reader.SetFileName(fileName)
		reader.Update()
		surf = reader.GetOutput()
	elif extension == ".stl":
		reader = vtk.vtkSTLReader()
		reader.SetFileName(fileName)
		reader.Update()
		surf = reader.GetOutput()
	elif extension == ".off":
		reader = OFFReader()
		reader.SetFileName(fileName)
		reader.Update()
		surf = reader.GetOutput()
	elif extension == ".obj":
		if os.path.exists(fname + ".mtl"):
			obj_import = vtk.vtkOBJImporter()
			obj_import.SetFileName(fileName)
			obj_import.SetFileNameMTL(fname + ".mtl")
			textures_path = os.path.normpath(os.path.dirname(fname) + "/../images")
			if os.path.exists(textures_path):
				obj_import.SetTexturePath(textures_path)
			obj_import.Read()

			actors = obj_import.GetRenderer().GetActors()
			actors.InitTraversal()
			append = vtk.vtkAppendPolyData()

			for i in range(actors.GetNumberOfItems()):
				surfActor = actors.GetNextActor()
				append.AddInputData(surfActor.GetMapper().GetInputAsDataSet())
			
			append.Update()
			surf = append.GetOutput()
			
		else:
			reader = vtk.vtkOBJReader()
			reader.SetFileName(fileName)
			reader.Update()
			surf = reader.GetOutput()

	return surf

def GetActor(surf):
	surfMapper = vtk.vtkPolyDataMapper()
	surfMapper.SetInputData(surf)

	############
	surfMapper.SetScalarRange(0.0,1.0)
	
	#build lookup table
	lut = vtk.vtkLookupTable()
	lut.SetTableRange(0.0, 1.0)

	lut.SetNumberOfColors(3)
	lut.SetTableValue(0, 1.0, 0.0, 0.0) # Red
	lut.SetTableValue(1, 1.0, 0.75, 0.0) # Amber
	lut.SetTableValue(2, 0.0, 1.0, 0.0) # Green

	lut.Build()

	#QUESTION: How do we get lut to reference region ids (from vtk file)
	surfMapper.SetLookupTable(lut)
	surfMapper.SetScalarModeToUseCellData()
	###########

	surfActor = vtk.vtkActor()
	surfActor.SetMapper(surfMapper)

	return surfActor

def RotateSurf(surf, rotationAngle, rotationVector):
	print("angle:", rotationAngle, "vector:", rotationVector)
	transform = vtk.vtkTransform()
	transform.RotateWXYZ(rotationAngle, rotationVector[0], rotationVector[1], rotationVector[2]);

	transformFilter = vtk.vtkTransformPolyDataFilter()
	transformFilter.SetTransform(transform)
	transformFilter.SetInputData(surf)
	transformFilter.Update()
	return transformFilter.GetOutput()

def GetUnitActor(fileName, random_rotation=False, normal_shaders=True):

	try:

		surf = ReadSurf(fileName)

		surf, surf_mean, surf_scale = Normalization(surf)

		if(random_rotation):
			rotationVector = np.random.random(3)*2.0 - 1.0
			rotationVector = rotationVector/np.linalg.norm(rotationVector)
			rotationAngle = np.random.random()*360.0
			surf = RotateSurf(surf, rotationAngle, rotationVector)

		if(normal_shaders):
			normals = vtk.vtkPolyDataNormals()
			normals.SetInputData(surf);
			normals.ComputeCellNormalsOff();
			normals.ComputePointNormalsOn();
			# normals.AutoOrientNormalsOn();
			normals.SplittingOff();
			normals.Update()
			surf = normals.GetOutput()

		# mapper
		surfActor = GetActor(surf)

		if(normal_shaders):

			sp = surfActor.GetShaderProperty();
			sp.AddVertexShaderReplacement(
				"//VTK::Normal::Dec",
				True,
				"//VTK::Normal::Dec\n" + 
				"  varying vec3 myNormalMCVSOutput;\n",
				False
			)

			sp.AddVertexShaderReplacement(
				"//VTK::Normal::Impl",
				True,
				"//VTK::Normal::Impl\n" +
				"  myNormalMCVSOutput = normalMC;\n",
				False
			)

			sp.AddVertexShaderReplacement(
				"//VTK::Color::Impl",
				True, "VTK::Color::Impl\n", False)

			sp.ClearVertexShaderReplacement("//VTK::Color::Impl", True)

			sp.AddFragmentShaderReplacement(
				"//VTK::Normal::Dec",
				True,
				"//VTK::Normal::Dec\n" + 
				"  varying vec3 myNormalMCVSOutput;\n",
				False
			)

			sp.AddFragmentShaderReplacement(
				"//VTK::Normal::Impl",
				True,
				"//VTK::Normal::Impl\n" +
				"  diffuseColor = myNormalMCVSOutput*0.5f + 0.5f;\n",
				False
			)

		return surfActor
	except Exception as e:
		print(e, file=sys.stderr)
		return None

def GetImage(img_np):
	img_np_shape = np.shape(img_np)
	ComponentType = itk.ctype('float')

	Dimension = img_np.ndim - 1
	PixelDimension = img_np.shape[-1]
	print("Dimension:", Dimension, "PixelDimension:", PixelDimension)

	if Dimension == 1:
		OutputImageType = itk.VectorImage[ComponentType, 2]
	else:
		OutputImageType = itk.VectorImage[ComponentType, Dimension]
	
	out_img = OutputImageType.New()
	out_img.SetNumberOfComponentsPerPixel(PixelDimension)

	size = itk.Size[OutputImageType.GetImageDimension()]()
	size.Fill(1)
	
	prediction_shape = list(img_np.shape[0:-1])
	prediction_shape.reverse()

	if Dimension == 1:
		size[1] = prediction_shape[0]
	else:
		for i, s in enumerate(prediction_shape):
			size[i] = s

	index = itk.Index[OutputImageType.GetImageDimension()]()
	index.Fill(0)

	RegionType = itk.ImageRegion[OutputImageType.GetImageDimension()]
	region = RegionType()
	region.SetIndex(index)
	region.SetSize(size)

	out_img.SetRegions(region)
	out_img.Allocate()

	out_img_np = itk.GetArrayViewFromImage(out_img)
	out_img_np.setfield(img_np.reshape(out_img_np.shape), out_img_np.dtype)

	return out_img
