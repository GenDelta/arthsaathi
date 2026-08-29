import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ScamScannerPage from "./page";
import { scamApi } from "@/lib/api/scam";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

// Mock api-client for scam
jest.mock("@/lib/api/scam", () => ({
  scamApi: {
    uploadDocument: jest.fn(),
    verifyDocument: jest.fn(),
    getStatus: jest.fn(),
  },
}));

// Mock zustand store
jest.mock("@/store/useAuthStore", () => ({
  useAuthStore: jest.fn(),
}));

describe("ScamScannerPage", () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: true,
    });
  });

  it("redirects if not authenticated", () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      isAuthenticated: false,
    });
    
    render(<ScamScannerPage />);
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("renders upload step initially", () => {
    render(<ScamScannerPage />);
    expect(screen.getByRole("heading", { name: /Scan a Document/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Extract Text/i })).toBeInTheDocument();
  });

  it("handles successful file upload and moves to verify step", async () => {
    (scamApi.uploadDocument as jest.Mock).mockResolvedValue({
      document_id: "test-doc-123",
      status: "PENDING_VERIFICATION",
      extracted_text: "Fake extracted text",
    });

    render(<ScamScannerPage />);
    
    // Create a fake file
    const file = new File(["fake content"], "test.png", { type: "image/png" });
    const fileInput = screen.getByLabelText(/Document Image/i);
    
    await userEvent.upload(fileInput, file);
    
    fireEvent.click(screen.getByRole("button", { name: /Extract Text/i }));

    await waitFor(() => {
      expect(scamApi.uploadDocument).toHaveBeenCalledWith(file);
      // It should move to VERIFY step
      expect(screen.getByRole("heading", { name: /Verify Extracted Text/i })).toBeInTheDocument();
      // Should populate textarea with OCR text
      expect(screen.getByDisplayValue("Fake extracted text")).toBeInTheDocument();
    });
  });

  it("handles verification and moves to analyzing step", async () => {
    (scamApi.uploadDocument as jest.Mock).mockResolvedValue({
      document_id: "test-doc-123",
      status: "PENDING_VERIFICATION",
      extracted_text: "Fake extracted text",
    });
    
    (scamApi.verifyDocument as jest.Mock).mockResolvedValue({});

    render(<ScamScannerPage />);
    
    // Simulate upload step completion
    const file = new File(["fake content"], "test.png", { type: "image/png" });
    const fileInput = screen.getByLabelText(/Document Image/i);
    await userEvent.upload(fileInput, file);
    fireEvent.click(screen.getByRole("button", { name: /Extract Text/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Verify Extracted Text/i })).toBeInTheDocument();
    });

    // Verify step
    fireEvent.click(screen.getByRole("button", { name: /Analyze for Scams/i }));

    await waitFor(() => {
      expect(scamApi.verifyDocument).toHaveBeenCalledWith("test-doc-123", "Fake extracted text");
      expect(screen.getByRole("heading", { name: /Analyzing Document.../i })).toBeInTheDocument();
    });
  });
});
