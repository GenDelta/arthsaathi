import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "./page";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

// Mock api-client
jest.mock("@/lib/api-client", () => ({
  authApi: {
    login: jest.fn(),
  },
}));

// Mock zustand store
jest.mock("@/store/useAuthStore", () => ({
  useAuthStore: jest.fn(),
}));

describe("LoginPage", () => {
  const mockPush = jest.fn();
  const mockReplace = jest.fn();
  const mockSetAuth = jest.fn();
  const mockFetchMe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
    });
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      setAuth: mockSetAuth,
      fetchMe: mockFetchMe,
    });
  });

  it("renders the login form correctly in Hindi by default", () => {
    render(<LoginPage />);
    expect(screen.getByRole("heading", { name: /वापस आपका स्वागत है/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /लॉगिन करें/i })).toBeInTheDocument();
  });

  it("handles successful login", async () => {
    (authApi.login as jest.Mock).mockResolvedValue({
      access_token: "fake-access",
      refresh_token: "fake-refresh",
      role: "CITIZEN",
    });

    render(<LoginPage />);
    
    await userEvent.type(screen.getByLabelText(/मोबाइल नंबर/i), "9876543210");
    await userEvent.type(screen.getByLabelText(/पासवर्ड/i), "password123");
    
    fireEvent.click(screen.getByRole("button", { name: /लॉगिन करें/i }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        phone_number: "+919876543210",
        password: "password123",
      });
      expect(mockSetAuth).toHaveBeenCalled();
      expect(mockFetchMe).toHaveBeenCalled();
      expect(mockReplace).toHaveBeenCalledWith("/");
    });
  });
});
